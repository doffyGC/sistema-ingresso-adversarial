"""População A1: compradores legítimos, sem estratégia (#9).

Cada comprador chega num tick sorteado, procura ingressos, reserva, demora um tempo próprio
para pagar e, se não consegue, tenta de novo, entra na fila ou desiste. A variação entre eles
vem dos parâmetros de ``[populacao_a1]`` e é toda sorteada pela semente:

- parte não tem cartão: com R3 ligado, a pré-autorização recusa e ele tende a desistir;
- parte é "ansiosa": age a cada tick e, com limite de requisições, leva 429 (falso positivo, P3);
- quem demora mais que o TTL para pagar perde a reserva ("prazo curto") e pode desistir;
- depois de algumas tentativas sem sucesso, desiste ou entra na fila.

Os compradores só usam as operações públicas da Borda e só leem ``RespostaBorda``.
"""

import random
from dataclasses import dataclass

from ..config import Parametros, PopulacaoA1
from ..contratos import Categoria, RespostaBorda
from .identidades import Identidades

# Fases de um comprador
ESPERANDO = "esperando"  # ainda não chegou
PROCURANDO = "procurando"
PAGANDO = "pagando"
FIM = "fim"  # comprou o que queria ou desistiu


@dataclass
class ReservaEmPagamento:
    reserva_id: str
    expira_em: int  # prazo informado pela Borda ao reservar
    iniciar_em: int  # tick em que começa a autenticação do pagamento (R4)
    pagar_em: int
    iniciado: bool = False


class CompradorA1:
    def __init__(
        self,
        conta: str,
        cluster: str,
        tem_cartao: bool,
        ansioso: bool,
        chegada: int,
        tempo_pagar: int,
        quantidade: int,
        perfil: PopulacaoA1,
        sorteio: random.Random,
    ):
        self.conta = conta
        self.cluster = cluster
        self.tem_cartao = tem_cartao
        self.ansioso = ansioso
        self.chegada = chegada
        self.tempo_pagar = tempo_pagar
        self.quantidade = quantidade  # quantos ingressos quer
        self.perfil = perfil
        self.sorteio = sorteio
        self.cadencia = perfil.cadencia_ansiosa if ansioso else perfil.cadencia_normal

        self.fase = ESPERANDO
        self.na_fila = False
        self.falhas = 0
        self.reserva: ReservaEmPagamento | None = None
        self.comprados = 0
        self.desistiu: str | None = None  # "fila", "oferta", "prazo" ou "verificacao"
        self.proxima_acao = chegada
        self.pedidos = 0  # numera as chaves de idempotência

    # ------------------------------------------------------------------

    def cadastrar(self, borda) -> None:
        borda.cadastrar(self.conta, self.cluster, self.tem_cartao)

    def agir(self, tick: int, borda) -> None:
        if self.fase == FIM or tick < self.chegada:
            return
        if self.fase == ESPERANDO:
            self.fase = PROCURANDO

        if self.fase == PAGANDO:
            reserva = self.reserva
            pediu = self.pagar(tick, borda)  # pagar vem antes: é a ação que importa
            if self.ansioso and not pediu and self.fase == PAGANDO:
                # Nos ticks sem pagamento, o ansioso fica conferindo a reserva: é a
                # cadência alta que um limite de requisições confunde com bot (P3).
                borda.consultar_reserva(self.conta, reserva.reserva_id)
            return

        if tick < self.proxima_acao:
            return
        self.proxima_acao = tick + self.cadencia

        if self.na_fila and self.olhar_fila(tick, borda):
            return
        self.procurar(tick, borda)

    # ------------------------------------------------------------------

    def chave(self, operacao: str) -> str:
        self.pedidos += 1
        return f"{self.conta}-{operacao}-{self.pedidos}"

    def procurar(self, tick: int, borda) -> None:
        resposta = borda.ver_disponiveis(self.conta)
        if not resposta.ok:
            self.tratar_rejeicao(resposta, borda)
            return
        ingressos = resposta.dados["ingressos"]
        if not ingressos:
            self.falhar(borda)
            return

        premium = [i for i in ingressos if i["setor"] == "premium"]
        if premium and self.sorteio.random() < self.perfil.preferencia_premium:
            escolhido = self.sorteio.choice(premium)
        else:
            escolhido = self.sorteio.choice(ingressos)

        resposta = borda.reservar(self.conta, escolhido["id"], chave=self.chave("reservar"))
        if resposta.ok:
            self.comecar_pagamento(tick, resposta)
        else:
            self.tratar_rejeicao(resposta, borda)

    def olhar_fila(self, tick: int, borda) -> bool:
        """Confere se chegou oferta. Devolve True se a ação do tick foi gasta aqui."""
        resposta = borda.consultar_fila(self.conta)
        if resposta.categoria == Categoria.LIMITE_REQUISICOES:
            return True  # a ação do tick já foi gasta; tenta de novo na próxima
        if not resposta.ok:
            return False
        oferta = resposta.dados.get("oferta")
        if oferta is None:
            if resposta.dados.get("posicao") is None:
                self.na_fila = False  # saiu da fila (a oferta venceu antes de ele ver)
            return False

        self.na_fila = False  # quem responde a uma oferta sai da fila
        if self.sorteio.random() < self.perfil.aceita_oferta:
            aceite = borda.responder_oferta(self.conta, oferta["ingresso_id"], True, chave=self.chave("oferta"))
            if aceite.ok and "reserva_id" in aceite.dados:
                self.comecar_pagamento(tick, aceite)
            else:
                self.tratar_rejeicao(aceite, borda)
        else:
            borda.responder_oferta(self.conta, oferta["ingresso_id"], False, chave=self.chave("oferta"))
            self.desistir("oferta")  # esperou na fila, mas recusou quando chegou a vez
        return True

    def comecar_pagamento(self, tick: int, resposta: RespostaBorda) -> None:
        self.fase = PAGANDO
        self.falhas = 0
        self.reserva = ReservaEmPagamento(
            reserva_id=resposta.dados["reserva_id"],
            expira_em=resposta.dados["expira_em"],
            iniciar_em=tick + self.tempo_pagar // 2,
            pagar_em=tick + self.tempo_pagar,
        )

    def tentar_de_novo(self, resposta: RespostaBorda, tick: int, borda) -> bool:
        """A recusa não quer dizer que a reserva acabou: vale repetir no próximo tick.

        Um 429 só barra a requisição, a reserva continua ativa. Com R6, o 429 chega como
        REJEITADA genérica e o comprador não sabe o motivo: insiste enquanto o prazo que
        conhece não passou. Depois dele, consulta a reserva, porque o R4 pode ter
        prorrogado; se ela ainda está ativa, guarda o prazo novo e insiste.
        """
        if resposta.categoria == Categoria.LIMITE_REQUISICOES:
            return True
        if resposta.categoria != Categoria.REJEITADA:
            return False
        if tick < self.reserva.expira_em:
            return True
        consulta = borda.consultar_reserva(self.conta, self.reserva.reserva_id)
        if not consulta.ok:
            return True  # a consulta também foi barrada: não dá para saber ainda
        if consulta.dados["status"] != "ATIVA":
            return False
        self.reserva.expira_em = consulta.dados["expira_em"]
        return True

    def pagar(self, tick: int, borda) -> bool:
        """Inicia ou conclui o pagamento quando chega a hora. Devolve True se fez requisição."""
        reserva = self.reserva
        if not reserva.iniciado and tick >= reserva.iniciar_em:
            inicio = borda.iniciar_pagamento(self.conta, reserva.reserva_id, chave=f"{reserva.reserva_id}-inicio")
            reserva.iniciado = not self.tentar_de_novo(inicio, tick, borda)
            if tick < reserva.pagar_em:
                return True
        if tick < reserva.pagar_em:
            return False

        resposta = borda.pagar(self.conta, reserva.reserva_id, chave=f"{reserva.reserva_id}-pagamento")
        if not resposta.ok and self.tentar_de_novo(resposta, tick, borda):
            return True  # continua pagando e repete a mesma chave (a Borda não guarda o 429)
        self.reserva = None
        self.proxima_acao = tick + self.cadencia
        if resposta.ok:
            self.comprados += 1
            self.fase = FIM if self.comprados >= self.quantidade else PROCURANDO
        elif self.sorteio.random() < self.perfil.desistencia_prazo:
            self.desistir("prazo")  # a reserva expirou antes de ele conseguir pagar
        else:
            self.fase = PROCURANDO
        return True

    def tratar_rejeicao(self, resposta: RespostaBorda, borda) -> None:
        if resposta.categoria == Categoria.LIMITE_REQUISICOES:
            return  # espera e tenta de novo na próxima ação
        if resposta.categoria == Categoria.SEM_CARTAO:
            if self.sorteio.random() < self.perfil.desistencia_verificacao:
                self.desistir("verificacao")
                return
        self.falhar(borda)

    def falhar(self, borda) -> None:
        self.falhas += 1
        if self.falhas < self.perfil.tentativas_antes_da_fila or self.na_fila:
            return
        self.falhas = 0
        if self.sorteio.random() < self.perfil.desistencia_fila:
            self.desistir("fila")
            return
        resposta = borda.entrar_fila(self.conta)
        self.na_fila = resposta.ok

    def desistir(self, motivo: str) -> None:
        self.fase = FIM
        self.desistiu = motivo


def criar_populacao(parametros: Parametros, semente: int, identidades: Identidades) -> list[CompradorA1]:
    """Sorteia os compradores A1 da rodada. Mesma semente, mesma população."""
    perfil = parametros.populacao_a1
    total = parametros.simulacao.compradores_a1
    sorteio = random.Random(f"populacao:{semente}")

    sem_cartao = set(sorteio.sample(range(total), round(total * perfil.fracao_sem_cartao)))
    ansiosos = set(sorteio.sample(range(total), round(total * perfil.fracao_ansiosa)))
    # Poucos pagam devagar: a moda fica perto do mínimo, e a cauda passa do TTL.
    moda_pagar = perfil.pagar_min + (perfil.pagar_max - perfil.pagar_min) * 0.15

    compradores = []
    for n in range(total):
        compradores.append(
            CompradorA1(
                conta=identidades.nova_conta("A1"),
                cluster=identidades.novo_cluster(),  # cada pessoa é um cluster próprio
                tem_cartao=n not in sem_cartao,
                ansioso=n in ansiosos,
                chegada=sorteio.randint(0, perfil.chegada_max),
                tempo_pagar=round(sorteio.triangular(perfil.pagar_min, perfil.pagar_max, moda_pagar)),
                quantidade=sorteio.randint(perfil.ingressos_min, perfil.ingressos_max),
                perfil=perfil,
                sorteio=random.Random(f"a1:{semente}:{n}"),
            )
        )
    return compradores
