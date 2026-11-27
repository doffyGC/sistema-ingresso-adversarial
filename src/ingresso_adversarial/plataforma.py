"""Plataforma: o "mundo" em que os agentes agem (núcleo do ambiente).

Aqui ficam as regras de reserva, pagamento, expiração e fila de espera. Toda mudança no
estado de um ingresso é pedida ao Estoque (DA2).

Os compradores (A1 e A2) não chamam a Plataforma diretamente: passam pela Borda.
A3 só usa ``aplicar_politica``, ``rebaixar_na_fila`` e ``cancelar_venda``.

A simulação roda em um processo só e atende uma requisição por vez (D2). O tempo só anda
quando alguém chama ``avancar``. Com a mesma semente, tudo acontece igual.
"""

import random
from dataclasses import dataclass, field

from .config import Lote, Parametros
from .contratos import EstadoIngresso, Ingresso, PoliticaA3, Reserva, StatusReserva
from .estoque import Estoque
from .eventos import Log
from .fila import Fila

DISPONIVEL = EstadoIngresso.DISPONIVEL
RESERVADO = EstadoIngresso.RESERVADO
OFERTADO_FILA = EstadoIngresso.OFERTADO_FILA
VENDIDO = EstadoIngresso.VENDIDO


@dataclass
class Conta:
    id: str
    cluster: str  # grupo de contas correlacionadas (mesmo dispositivo, cartão...)
    tem_cartao: bool = True


@dataclass
class Oferta:
    conta: str
    prazo: int  # tick em que a oferta vence


@dataclass
class Resultado:
    """O que a Plataforma devolve para a Borda. O motivo é sempre o exato (DA5)."""

    ok: bool
    motivo: str | None = None  # por que foi rejeitado (ver lista abaixo)
    dados: dict = field(default_factory=dict)
    criou: bool = False  # a Borda responde 201 quando algo foi criado


# Motivos de rejeição
CONTA_NAO_CADASTRADA = "CONTA_NAO_CADASTRADA"
CONTA_JA_CADASTRADA = "CONTA_JA_CADASTRADA"
INGRESSO_NAO_EXISTE = "INGRESSO_NAO_EXISTE"
INGRESSO_INDISPONIVEL = "INGRESSO_INDISPONIVEL"
LIMITE_POR_CONTA = "LIMITE_POR_CONTA"
R2_LIMITE_CONTA = "R2_LIMITE_CONTA"
R2_LIMITE_CLUSTER = "R2_LIMITE_CLUSTER"
R3_SEM_CARTAO = "R3_SEM_CARTAO"
RESERVA_NAO_EXISTE = "RESERVA_NAO_EXISTE"
RESERVA_NAO_ATIVA = "RESERVA_NAO_ATIVA"
JA_ESTA_NA_FILA = "JA_ESTA_NA_FILA"
SEM_OFERTA = "SEM_OFERTA"
LIMITE_REQUISICOES = "LIMITE_REQUISICOES"  # usado pela Borda


def criar_lote(lote: Lote) -> list[Ingresso]:
    ingressos = []
    for numero in range(1, lote.quantidade + 1):
        if numero <= lote.premium:
            ingressos.append(Ingresso(id=numero, setor="premium", preco=lote.preco_premium))
        else:
            ingressos.append(Ingresso(id=numero, setor="pista", preco=lote.preco_pista))
    return ingressos


class Plataforma:
    def __init__(self, parametros=None, politica=None, semente=None, log=None, rodada=None):
        self.parametros = parametros or Parametros()
        self.semente = semente if semente is not None else self.parametros.simulacao.semente
        self.tick = 0

        self.log = log or Log()
        self.log.tick = 0
        if rodada is not None:
            self.log.rodada = rodada

        self.estoque = Estoque(criar_lote(self.parametros.lote), self.log)
        self.fila = Fila(random.Random(self.semente))
        self.contas: dict[str, Conta] = {}
        self.reservas: dict[str, Reserva] = {}
        self.ofertas: dict[int, Oferta] = {}  # ingresso_id -> oferta em aberto
        self.cobrancas: list[str] = []  # ids das reservas cobradas (pagamento simulado)
        self.expiracoes: dict[str, int] = {}  # conta -> quantas reservas deixou expirar
        self.aguardando_fila: list[int] = []  # ingressos em OFERTADO_FILA esperando a vez

        self.politica = PoliticaA3()
        self.aplicar_politica(politica or self.parametros.politica_inicial)

    # ------------------------------------------------------------------
    # Política de A3
    # ------------------------------------------------------------------

    def aplicar_politica(self, politica: PoliticaA3) -> None:
        """Liga, desliga ou ajusta os controles. Reservas já feitas mantêm o prazo delas."""
        self.politica = politica
        self.log.registrar("politica", quem="A3", politica=politica.model_dump(), ligados=politica.controles_ligados())
        for conta in self.fila.ordem():
            self.aplicar_r5(conta)
        self.atender_aguardando()  # os limites mudaram: quem é elegível pode ter mudado

    # ------------------------------------------------------------------
    # Consultas auxiliares
    # ------------------------------------------------------------------

    def reservas_ativas(self) -> list[Reserva]:
        return [r for r in self.reservas.values() if r.status == StatusReserva.ATIVA]

    def ativas_da_conta(self, conta: str) -> int:
        return len([r for r in self.reservas_ativas() if r.conta == conta])

    def ativas_do_cluster(self, cluster: str) -> int:
        return len([r for r in self.reservas_ativas() if r.cluster == cluster])

    def compradas_pela_conta(self, conta: str) -> int:
        return len([i for i in self.estoque.ingressos.values() if i.dono == conta])

    def disponibilidade(self) -> list[Ingresso]:
        """F1: só mostra ingressos DISPONIVEL. Um ingresso ofertado à fila não aparece (R1)."""
        return self.estoque.no_estado(DISPONIVEL)

    def motivo_para_recusar(self, conta: Conta):
        """Confere as regras de limite. Devolve (motivo, informações) ou None se pode reservar."""
        p = self.politica
        ativas = self.ativas_da_conta(conta.id)
        total = ativas + self.compradas_pela_conta(conta.id)

        if total >= p.limite_por_conta:
            return LIMITE_POR_CONTA, {"limite": p.limite_por_conta}
        if p.r2.ativo and ativas >= p.r2.max_por_conta:
            return R2_LIMITE_CONTA, {"limiar": p.r2.max_por_conta}
        if p.r2.ativo and self.ativas_do_cluster(conta.cluster) >= p.r2.max_por_cluster:
            return R2_LIMITE_CLUSTER, {"limiar": p.r2.max_por_cluster, "cluster": conta.cluster}
        if p.r3.ativo and not conta.tem_cartao:
            return R3_SEM_CARTAO, {}
        return None

    # ------------------------------------------------------------------
    # Cadastro
    # ------------------------------------------------------------------

    def cadastrar(self, conta: str, cluster: str, tem_cartao: bool = True) -> Resultado:
        if conta in self.contas:
            return Resultado(False, CONTA_JA_CADASTRADA)
        self.contas[conta] = Conta(conta, cluster, tem_cartao)
        self.log.registrar("cadastro", quem=conta, cluster=cluster, tem_cartao=tem_cartao)
        return Resultado(True, criou=True, dados={"conta": conta})

    # ------------------------------------------------------------------
    # Reserva (F2): limite por conta, R2, R3
    # ------------------------------------------------------------------

    def reservar(self, conta_id: str, ingresso_id: int) -> Resultado:
        conta = self.contas.get(conta_id)
        if conta is None:
            return Resultado(False, CONTA_NAO_CADASTRADA)
        if ingresso_id not in self.estoque.ingressos:
            return self.recusar_reserva(conta_id, ingresso_id, INGRESSO_NAO_EXISTE, {})
        if self.estoque.estado(ingresso_id) != DISPONIVEL:
            return self.recusar_reserva(conta_id, ingresso_id, INGRESSO_INDISPONIVEL, {})

        recusa = self.motivo_para_recusar(conta)
        if recusa is not None:
            motivo, info = recusa
            return self.recusar_reserva(conta_id, ingresso_id, motivo, info)

        reserva = self.criar_reserva(conta, ingresso_id, veio_da_fila=False)
        return Resultado(True, criou=True, dados=self.dados_da_reserva(reserva))

    def recusar_reserva(self, conta: str, ingresso_id: int, motivo: str, info: dict) -> Resultado:
        self.log.registrar("reserva_rejeitada", quem=conta, ingresso=ingresso_id, motivo=motivo, **info)
        return Resultado(False, motivo, dados=info)

    def criar_reserva(self, conta: Conta, ingresso_id: int, veio_da_fila: bool) -> Reserva:
        reserva = Reserva(
            id=f"R{len(self.reservas) + 1:04d}",
            ingresso_id=ingresso_id,
            conta=conta.id,
            cluster=conta.cluster,
            criada_em=self.tick,
            expira_em=self.tick + self.politica.ttl,
            veio_da_fila=veio_da_fila,
            custo_pre_autorizacao=self.politica.r3.custo if self.politica.r3.ativo else 0.0,
        )
        # Primeiro o Estoque muda o estado. Se ele recusar, a reserva não é guardada.
        self.estoque.mudar_estado(ingresso_id, RESERVADO, "reserva", reserva_id=reserva.id)
        self.reservas[reserva.id] = reserva
        self.log.registrar(
            "reserva",
            quem=conta.id,
            reserva=reserva.id,
            ingresso=ingresso_id,
            cluster=conta.cluster,
            veio_da_fila=veio_da_fila,
            expira_em=reserva.expira_em,
            custo_pre_autorizacao=reserva.custo_pre_autorizacao,
        )
        return reserva

    def dados_da_reserva(self, reserva: Reserva) -> dict:
        return {
            "reserva_id": reserva.id,
            "ingresso_id": reserva.ingresso_id,
            "status": reserva.status.value,
            "expira_em": reserva.expira_em,
            "tempo_restante": max(0, reserva.expira_em - self.tick),
            "custo_pre_autorizacao": reserva.custo_pre_autorizacao,
        }

    def buscar_reserva(self, conta_id: str, reserva_id: str):
        """Devolve a reserva se ela existir e for da conta; senão, um Resultado de erro."""
        if conta_id not in self.contas:
            return Resultado(False, CONTA_NAO_CADASTRADA)
        reserva = self.reservas.get(reserva_id)
        # Reserva de outra pessoa responde igual a inexistente, para não vazar informação.
        if reserva is None or reserva.conta != conta_id:
            return Resultado(False, RESERVA_NAO_EXISTE)
        return reserva

    def consultar_reserva(self, conta_id: str, reserva_id: str) -> Resultado:
        reserva = self.buscar_reserva(conta_id, reserva_id)
        if isinstance(reserva, Resultado):
            return reserva
        return Resultado(True, dados=self.dados_da_reserva(reserva))

    # ------------------------------------------------------------------
    # Pagamento (F4): simulado
    # ------------------------------------------------------------------

    def iniciar_pagamento(self, conta_id: str, reserva_id: str) -> Resultado:
        """Começa a autenticação bancária. É isso que permite a prorrogação do R4."""
        reserva = self.buscar_reserva(conta_id, reserva_id)
        if isinstance(reserva, Resultado):
            return reserva
        if reserva.status != StatusReserva.ATIVA:
            return Resultado(False, RESERVA_NAO_ATIVA)
        if not reserva.pagamento_iniciado:
            reserva.pagamento_iniciado = True
            self.log.registrar("pagamento_iniciado", quem=conta_id, reserva=reserva.id)
        return Resultado(True, dados=self.dados_da_reserva(reserva))

    def pagar(self, conta_id: str, reserva_id: str) -> Resultado:
        reserva = self.buscar_reserva(conta_id, reserva_id)
        if isinstance(reserva, Resultado):
            return reserva
        if reserva.status != StatusReserva.ATIVA:
            return Resultado(False, RESERVA_NAO_ATIVA)

        self.estoque.mudar_estado(reserva.ingresso_id, VENDIDO, "pagamento", dono=conta_id)
        reserva.status = StatusReserva.PAGA
        reserva.pagamento_iniciado = True
        self.cobrancas.append(reserva.id)
        preco = self.estoque.ingressos[reserva.ingresso_id].preco
        self.log.registrar("pagamento", quem=conta_id, reserva=reserva.id, ingresso=reserva.ingresso_id, valor=preco)
        return Resultado(True, dados={**self.dados_da_reserva(reserva), "valor": preco})

    # ------------------------------------------------------------------
    # Fila de espera (F6) e R5
    # ------------------------------------------------------------------

    def entrar_fila(self, conta_id: str) -> Resultado:
        if conta_id not in self.contas:
            return Resultado(False, CONTA_NAO_CADASTRADA)
        if conta_id in self.fila:
            return Resultado(False, JA_ESTA_NA_FILA)
        self.fila.entrar(conta_id)
        self.log.registrar("fila_entrada", quem=conta_id)
        self.aplicar_r5(conta_id)
        self.atender_aguardando()
        return Resultado(True, dados={"posicao": self.fila.posicao(conta_id)})

    def consultar_fila(self, conta_id: str) -> Resultado:
        if conta_id not in self.contas:
            return Resultado(False, CONTA_NAO_CADASTRADA)
        oferta = None
        for ingresso_id, o in self.ofertas.items():
            if o.conta == conta_id:
                oferta = {"ingresso_id": ingresso_id, "prazo": o.prazo}
        return Resultado(True, dados={"posicao": self.fila.posicao(conta_id), "oferta": oferta})

    def aplicar_r5(self, conta: str) -> None:
        """R5: quem deixou expirar várias reservas vai para o fim da fila (sem bloqueio)."""
        r5 = self.politica.r5
        if r5.ativo and self.expiracoes.get(conta, 0) >= r5.limiar_expiracoes:
            if self.fila.rebaixar(conta):
                self.log.registrar("rebaixamento", quem="sistema", conta=conta, motivo="R5")

    def rebaixar_na_fila(self, conta: str, motivo: str) -> bool:
        """Para A3 usar quando o Detector marcar uma conta (#11)."""
        if self.fila.rebaixar(conta):
            self.log.registrar("rebaixamento", quem="A3", conta=conta, motivo=motivo)
            return True
        return False

    # ------------------------------------------------------------------
    # Redistribuição (R1): para onde vai um ingresso liberado
    # ------------------------------------------------------------------

    def elegiveis_na_fila(self) -> list[str]:
        """Contas da fila que poderiam receber um ingresso, com ou sem oferta aberta (DA1)."""
        return [c for c in self.fila.ordem() if self.motivo_para_recusar(self.contas[c]) is None]

    def proximo_da_fila(self) -> str | None:
        """Primeira conta elegível da fila que ainda não tem oferta aberta."""
        contas_com_oferta = {o.conta for o in self.ofertas.values()}
        for conta_id in self.elegiveis_na_fila():
            if conta_id not in contas_com_oferta:  # cada conta recebe uma oferta por vez
                return conta_id
        return None

    def redistribuir(self, ingresso_id: int, usar_fila: bool) -> None:
        """Decide para onde vai um ingresso liberado.

        Com a fila: oferta à próxima conta elegível livre. Se todas as elegíveis já estão
        com uma oferta aberta, o ingresso espera a vez em OFERTADO_FILA, fora da
        disponibilidade (critério 3). Só volta ao público quando não há mais ninguém
        elegível na fila (DA1).
        """
        if usar_fila:
            conta = self.proximo_da_fila()
            if conta is not None:
                prazo = self.tick + self.politica.r1.prazo_oferta
                self.estoque.mudar_estado(ingresso_id, OFERTADO_FILA, "oferta à fila", ofertado_para=conta)
                self.ofertas[ingresso_id] = Oferta(conta, prazo)
                self.log.registrar("oferta", quem="sistema", ingresso=ingresso_id, conta=conta, prazo=prazo)
                return
            if self.elegiveis_na_fila():
                ingresso = self.estoque.ingressos[ingresso_id]
                if not (ingresso.estado == OFERTADO_FILA and ingresso.ofertado_para is None):
                    self.estoque.mudar_estado(ingresso_id, OFERTADO_FILA, "aguarda a vez na fila")
                    self.log.registrar("aguardando_fila", quem="sistema", ingresso=ingresso_id)
                self.aguardando_fila.append(ingresso_id)
                return

        self.estoque.mudar_estado(ingresso_id, DISPONIVEL, "volta ao estoque público")
        self.log.registrar(
            "volta_ao_publico",
            quem="sistema",
            ingresso=ingresso_id,
            pela_fila=usar_fila,
            elegiveis_na_fila=len(self.elegiveis_na_fila()) if usar_fila else 0,
        )

    def atender_aguardando(self) -> None:
        """Tenta de novo os ingressos que esperavam a vez na fila.

        Se A3 desligou o R1 enquanto eles esperavam, voltam ao público (a fila deixou de valer).
        """
        pendentes, self.aguardando_fila = self.aguardando_fila, []
        for ingresso_id in pendentes:
            self.redistribuir(ingresso_id, usar_fila=self.politica.r1.ativo)

    def responder_oferta(self, conta_id: str, ingresso_id: int, aceitar: bool) -> Resultado:
        conta = self.contas.get(conta_id)
        if conta is None:
            return Resultado(False, CONTA_NAO_CADASTRADA)
        oferta = self.ofertas.get(ingresso_id)
        if oferta is None or oferta.conta != conta_id:
            return Resultado(False, SEM_OFERTA)

        recusa = self.motivo_para_recusar(conta) if aceitar else None
        del self.ofertas[ingresso_id]
        self.fila.sair(conta_id)  # quem respondeu sai da fila
        self.log.registrar("oferta_respondida", quem=conta_id, ingresso=ingresso_id, aceitou=aceitar)

        if aceitar and recusa is None:
            reserva = self.criar_reserva(conta, ingresso_id, veio_da_fila=True)
            self.atender_aguardando()  # a conta saiu da fila: a vez passa adiante
            return Resultado(True, criou=True, dados=self.dados_da_reserva(reserva))

        # Recusou (ou não pode aceitar): a oferta passa ao próximo da fila.
        self.redistribuir(ingresso_id, usar_fila=True)
        self.atender_aguardando()
        if recusa is not None:
            motivo, info = recusa
            return Resultado(False, motivo, dados=info)
        return Resultado(True, dados={"recusou": True})

    # ------------------------------------------------------------------
    # Cancelamento a posteriori (a decisão é de A3, #11; aqui só a mecânica)
    # ------------------------------------------------------------------

    def cancelar_venda(self, ingresso_id: int, motivo: str, evidencia: dict) -> bool:
        if self.estoque.estado(ingresso_id) != VENDIDO:
            return False
        dono = self.estoque.ingressos[ingresso_id].dono
        self.log.registrar("cancelamento", quem="A3", ingresso=ingresso_id, dono=dono, motivo=motivo, evidencia=evidencia)
        self.redistribuir(ingresso_id, usar_fila=True)
        return True

    # ------------------------------------------------------------------
    # Passagem do tempo: expiração (TTL, R4) e prazo das ofertas
    # ------------------------------------------------------------------

    def avancar(self, ticks: int = 1) -> None:
        for _ in range(ticks):
            self.tick += 1
            self.log.tick = self.tick
            self.expirar_reservas()
            self.vencer_ofertas()

    def expirar_reservas(self) -> None:
        vencidas = [r for r in self.reservas_ativas() if r.expira_em <= self.tick]
        for reserva in vencidas:
            r4 = self.politica.r4
            # R4: se o pagamento já começou, ganha mais tempo uma única vez.
            if r4.ativo and reserva.pagamento_iniciado and not reserva.prorrogada:
                reserva.expira_em += r4.prorrogacao
                reserva.prorrogada = True
                self.log.registrar("prorrogacao", quem="sistema", reserva=reserva.id, expira_em=reserva.expira_em)
                continue

            reserva.status = StatusReserva.EXPIRADA
            self.expiracoes[reserva.conta] = self.expiracoes.get(reserva.conta, 0) + 1
            self.log.registrar("expiracao", quem="sistema", reserva=reserva.id, ingresso=reserva.ingresso_id, conta=reserva.conta)
            self.aplicar_r5(reserva.conta)
            # R1 ligado: vai para a fila. R1 desligado: volta ao público (é a falha PE3).
            self.redistribuir(reserva.ingresso_id, usar_fila=self.politica.r1.ativo)

    def vencer_ofertas(self) -> None:
        vencidas = [i for i, o in self.ofertas.items() if o.prazo <= self.tick]
        for ingresso_id in vencidas:
            conta = self.ofertas.pop(ingresso_id).conta
            self.fila.sair(conta)  # não respondeu a tempo: sai da fila (garante o INV5)
            self.log.registrar("oferta_vencida", quem="sistema", ingresso=ingresso_id, conta=conta)
            self.redistribuir(ingresso_id, usar_fila=True)
        self.atender_aguardando()

    # ------------------------------------------------------------------
    # Invariantes (docs/decisoes-arquitetura.md)
    # ------------------------------------------------------------------

    def verificar_invariantes(self) -> list[str]:
        """Confere INV1 a INV6. Devolve a lista de problemas encontrados; lista vazia = tudo certo."""
        problemas = []
        ativas = self.reservas_ativas()

        for ingresso in self.estoque.ingressos.values():
            reservas_do_ingresso = [r for r in ativas if r.ingresso_id == ingresso.id]
            # INV2: no máximo uma reserva ativa por ingresso.
            if len(reservas_do_ingresso) > 1:
                problemas.append(f"INV2: ingresso {ingresso.id} tem {len(reservas_do_ingresso)} reservas ativas")
            # INV1: o estado combina com o resto dos dados.
            if (ingresso.estado == RESERVADO) != (len(reservas_do_ingresso) == 1):
                problemas.append(f"INV1: ingresso {ingresso.id} RESERVADO sem reserva (ou o contrário)")
            if (ingresso.estado == VENDIDO) != (ingresso.dono is not None):
                problemas.append(f"INV1: ingresso {ingresso.id} VENDIDO sem dono (ou o contrário)")
            na_fila = ingresso.id in self.ofertas or ingresso.id in self.aguardando_fila
            if (ingresso.estado == OFERTADO_FILA) != na_fila:
                problemas.append(f"INV1: ingresso {ingresso.id} OFERTADO_FILA sem oferta (ou o contrário)")

        # INV3: limites por conta e, com R2, por cluster.
        p = self.politica
        for conta in self.contas.values():
            if self.ativas_da_conta(conta.id) + self.compradas_pela_conta(conta.id) > p.limite_por_conta:
                problemas.append(f"INV3: conta {conta.id} passou do limite por conta")
            if p.r2.ativo and self.ativas_da_conta(conta.id) > p.r2.max_por_conta:
                problemas.append(f"INV3: conta {conta.id} passou do limite de reservas ativas")
        if p.r2.ativo:
            for cluster in {c.cluster for c in self.contas.values()}:
                if self.ativas_do_cluster(cluster) > p.r2.max_por_cluster:
                    problemas.append(f"INV3: cluster {cluster} passou do limite de reservas ativas")

        # INV4: com a fila, um ingresso só volta ao público quando não há ninguém elegível nela.
        for evento in self.log.do_tipo("volta_ao_publico"):
            if evento.dados["pela_fila"] and evento.dados["elegiveis_na_fila"] > 0:
                problemas.append(
                    f"INV4: ingresso {evento.dados['ingresso']} voltou ao público no tick {evento.tick} "
                    f"com {evento.dados['elegiveis_na_fila']} conta(s) elegível(is) na fila"
                )

        # INV5: nenhuma oferta fica parada depois do prazo.
        for ingresso_id, oferta in self.ofertas.items():
            if oferta.prazo <= self.tick:
                problemas.append(f"INV5: oferta do ingresso {ingresso_id} passou do prazo")
        # Quem espera a vez depende de uma oferta aberta, que tem prazo. Sem ela, ficaria preso.
        if self.aguardando_fila and not self.ofertas:
            problemas.append(f"INV5: ingressos {self.aguardando_fila} esperam a fila sem nenhuma oferta aberta")

        # INV6: cada reserva é cobrada no máximo uma vez, e só reservas pagas são cobradas.
        for reserva in self.reservas.values():
            vezes = self.cobrancas.count(reserva.id)
            if vezes > 1:
                problemas.append(f"INV6: reserva {reserva.id} cobrada {vezes} vezes")
            if (reserva.status == StatusReserva.PAGA) != (vezes == 1):
                problemas.append(f"INV6: reserva {reserva.id} com cobrança errada")

        return problemas
