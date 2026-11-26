"""Borda da API: a única porta de entrada dos compradores (A1 e o bot de A2).

Não é um servidor HTTP: são funções Python chamadas direto (D2). Em cada requisição:
1. se a chave de idempotência já foi usada, devolve a mesma resposta de antes (DA3);
2. aplica o limite de requisições, se A3 ligou;
3. confere se a conta está cadastrada;
4. chama a Plataforma;
5. traduz o resultado para o comprador: detalhado com R6 desligado, genérico com R6
   ligado (DA5). O motivo exato fica sempre no log.
"""

from . import plataforma as p
from .contratos import Categoria, RespostaBorda
from .plataforma import Plataforma, Resultado

MENSAGEM_GENERICA = "Não foi possível concluir a solicitação."

# Como cada motivo aparece para o comprador quando R6 está desligado.
# R2_LIMITE_CONTA e R2_LIMITE_CLUSTER têm a MESMA resposta e sem número:
# o comprador não descobre qual limiar disparou (critério 4).
RESPOSTAS = {
    p.CONTA_NAO_CADASTRADA: (401, Categoria.ERRO, "Conta não cadastrada."),
    p.CONTA_JA_CADASTRADA: (409, Categoria.ERRO, "Conta já cadastrada."),
    p.INGRESSO_NAO_EXISTE: (404, Categoria.ERRO, "Ingresso não encontrado."),
    p.INGRESSO_INDISPONIVEL: (409, Categoria.INDISPONIVEL, "Ingresso indisponível."),
    p.LIMITE_POR_CONTA: (403, Categoria.LIMITE_INGRESSOS, "Limite de ingressos por conta atingido."),
    p.R2_LIMITE_CONTA: (403, Categoria.LIMITE_RESERVAS, "Limite de reservas ativas atingido."),
    p.R2_LIMITE_CLUSTER: (403, Categoria.LIMITE_RESERVAS, "Limite de reservas ativas atingido."),
    p.R3_SEM_CARTAO: (402, Categoria.SEM_CARTAO, "Pré-autorização do cartão recusada."),
    p.RESERVA_NAO_EXISTE: (404, Categoria.ERRO, "Reserva não encontrada."),
    p.RESERVA_NAO_ATIVA: (409, Categoria.ERRO, "A reserva não está mais ativa."),
    p.JA_ESTA_NA_FILA: (409, Categoria.ERRO, "A conta já está na fila."),
    p.SEM_OFERTA: (404, Categoria.ERRO, "Não há oferta para esta conta."),
}


class Borda:
    def __init__(self, plataforma: Plataforma):
        self.plataforma = plataforma
        self.respostas_guardadas = {}  # (conta, operação, chave) -> RespostaBorda
        self.requisicoes_recentes = {}  # origem ou conta -> lista de ticks das requisições

    # ------------------------------------------------------------------
    # Operações que o comprador pode fazer
    # ------------------------------------------------------------------

    def cadastrar(self, conta, cluster, tem_cartao=True, origem=None):
        return self.atender(
            "cadastrar", conta, origem, None,
            lambda: self.plataforma.cadastrar(conta, cluster, tem_cartao),
            precisa_cadastro=False,
        )

    def ver_disponiveis(self, conta, origem=None):
        def executar():
            ingressos = self.plataforma.disponibilidade()
            lista = [{"id": i.id, "setor": i.setor, "preco": i.preco} for i in ingressos]
            return Resultado(True, dados={"ingressos": lista})

        return self.atender("ver_disponiveis", conta, origem, None, executar)

    def reservar(self, conta, ingresso_id, chave=None, origem=None):
        return self.atender(
            "reservar", conta, origem, chave,
            lambda: self.plataforma.reservar(conta, ingresso_id),
        )

    def consultar_reserva(self, conta, reserva_id, origem=None):
        return self.atender(
            "consultar_reserva", conta, origem, None,
            lambda: self.plataforma.consultar_reserva(conta, reserva_id),
        )

    def iniciar_pagamento(self, conta, reserva_id, chave=None, origem=None):
        return self.atender(
            "iniciar_pagamento", conta, origem, chave,
            lambda: self.plataforma.iniciar_pagamento(conta, reserva_id),
        )

    def pagar(self, conta, reserva_id, chave=None, origem=None):
        return self.atender(
            "pagar", conta, origem, chave,
            lambda: self.plataforma.pagar(conta, reserva_id),
        )

    def entrar_fila(self, conta, origem=None):
        return self.atender(
            "entrar_fila", conta, origem, None,
            lambda: self.plataforma.entrar_fila(conta),
        )

    def consultar_fila(self, conta, origem=None):
        return self.atender(
            "consultar_fila", conta, origem, None,
            lambda: self.plataforma.consultar_fila(conta),
        )

    def responder_oferta(self, conta, ingresso_id, aceitar, chave=None, origem=None):
        return self.atender(
            "responder_oferta", conta, origem, chave,
            lambda: self.plataforma.responder_oferta(conta, ingresso_id, aceitar),
        )

    # ------------------------------------------------------------------
    # O caminho de toda requisição
    # ------------------------------------------------------------------

    def atender(self, operacao, conta, origem, chave, executar, precisa_cadastro=True) -> RespostaBorda:
        origem = origem or conta
        log = self.plataforma.log

        # 1. Idempotência: mesma chave = mesma resposta, sem fazer nada de novo.
        if chave is not None and (conta, operacao, chave) in self.respostas_guardadas:
            log.registrar("repeticao", quem=conta, operacao=operacao, chave=chave)
            return self.respostas_guardadas[(conta, operacao, chave)]

        # 2 a 4. Limite de requisições, cadastro e a operação em si.
        if self.passou_do_limite(conta, origem):
            limite = self.plataforma.politica.limite_requisicoes
            info = {"maximo": limite.maximo, "janela": limite.janela, "por": limite.por}
            resultado = Resultado(False, p.LIMITE_REQUISICOES, dados=info)
        elif precisa_cadastro and conta not in self.plataforma.contas:
            resultado = Resultado(False, p.CONTA_NAO_CADASTRADA)
        else:
            resultado = executar()

        # 5. Tradução para o comprador.
        resposta = self.traduzir(resultado)
        log.registrar(
            "requisicao",
            quem=conta,
            operacao=operacao,
            origem=origem,
            motivo=resultado.motivo,  # o motivo exato fica no log interno (DA5)
            codigo=resposta.codigo,
            categoria=resposta.categoria.value,
        )

        # Guarda a resposta para repetições. Um 429 não é guardado, porque a operação
        # nem chegou a ser feita: o comprador pode tentar de novo depois.
        if chave is not None and resultado.motivo != p.LIMITE_REQUISICOES:
            self.respostas_guardadas[(conta, operacao, chave)] = resposta
        return resposta

    def passou_do_limite(self, conta, origem) -> bool:
        """Janela deslizante: conta as requisições aceitas nos últimos `janela` ticks."""
        limite = self.plataforma.politica.limite_requisicoes
        if not limite.ativo:
            return False
        agora = self.plataforma.tick
        quem = origem if limite.por == "origem" else conta
        recentes = [t for t in self.requisicoes_recentes.get(quem, []) if t > agora - limite.janela]
        if len(recentes) >= limite.maximo:
            self.requisicoes_recentes[quem] = recentes
            return True
        self.requisicoes_recentes[quem] = recentes + [agora]
        return False

    def traduzir(self, resultado: Resultado) -> RespostaBorda:
        tick = self.plataforma.tick

        if resultado.ok:
            codigo = 201 if resultado.criou else 200
            return RespostaBorda(ok=True, codigo=codigo, categoria=Categoria.OK, mensagem="OK", dados=resultado.dados, tick=tick)

        # R6 ligado: toda rejeição recebe a mesma resposta, menos "ingresso indisponível",
        # que é informação de estoque e não de detecção.
        if self.plataforma.politica.r6.ativo:
            if resultado.motivo == p.INGRESSO_INDISPONIVEL:
                return RespostaBorda(ok=False, codigo=409, categoria=Categoria.INDISPONIVEL, mensagem="Ingresso indisponível.", tick=tick)
            return RespostaBorda(ok=False, codigo=403, categoria=Categoria.REJEITADA, mensagem=MENSAGEM_GENERICA, tick=tick)

        # R6 desligado (estado inicial): o 429 mostra o limiar, como na rodada 1 do T1.
        if resultado.motivo == p.LIMITE_REQUISICOES:
            d = resultado.dados
            mensagem = f"Too Many Requests: máximo de {d['maximo']} requisições a cada {d['janela']} s por {d['por']}."
            return RespostaBorda(ok=False, codigo=429, categoria=Categoria.LIMITE_REQUISICOES, mensagem=mensagem, detalhe=d, tick=tick)

        codigo, categoria, mensagem = RESPOSTAS[resultado.motivo]
        detalhe = {}
        if resultado.motivo == p.LIMITE_POR_CONTA:
            # O limite de 4 por conta é uma regra anunciada: pode mostrar o número.
            detalhe = {"limite_por_conta": resultado.dados["limite"]}
        return RespostaBorda(ok=False, codigo=codigo, categoria=categoria, mensagem=mensagem, detalhe=detalhe, tick=tick)
