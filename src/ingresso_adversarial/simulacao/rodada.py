"""Uma rodada = uma abertura de vendas (D4, #9).

A rodada cria o ambiente, cadastra a população A1 e o bot de A2 e avança o relógio tick a
tick. Em cada tick, os participantes agem numa ordem sorteada pela semente; depois a
Plataforma aplica as expirações e o prazo das ofertas.

Os participantes nunca recebem a Borda de verdade: recebem uma ``BordaObservada``, que só
expõe as operações do comprador. Assim ninguém alcança a Plataforma por ``borda.plataforma``,
e as respostas recebidas pelo bot ficam guardadas para montar a ``ObservacaoA2``.
"""

import random
from dataclasses import dataclass, field
from typing import Any, Protocol

from .. import criar_ambiente
from ..borda import Borda
from ..config import Parametros
from ..contratos import PoliticaA3, RespostaBorda
from ..eventos import Log
from ..plataforma import Plataforma
from .identidades import Identidades, IdentidadesA2
from .populacao import CompradorA1, criar_populacao
from .telemetria import Telemetria

# O que um comprador pode pedir à Borda.
OPERACOES_DO_COMPRADOR = frozenset(
    {
        "cadastrar",
        "ver_disponiveis",
        "reservar",
        "consultar_reserva",
        "iniciar_pagamento",
        "pagar",
        "entrar_fila",
        "consultar_fila",
        "responder_oferta",
    }
)


@dataclass
class Pedido:
    """Uma requisição feita pelo participante e a resposta que ele recebeu."""

    operacao: str
    argumentos: dict[str, Any]
    resposta: RespostaBorda


class ContaNaoEmitida(Exception):
    """O participante tentou agir com uma conta que o ambiente não emitiu para ele."""


class BordaObservada:
    """Expõe só as operações do comprador e anota cada pedido e resposta.

    Só aceita requisições feitas com as contas do próprio participante (``contas``). Assim o
    bot não cadastra ids próprios nem age em nome de contas de A1.
    """

    def __init__(self, borda: Borda, contas: set[str], anotar: bool = True):
        self._borda = borda
        self._contas = contas  # conjunto vivo: cresce à medida que o ambiente emite contas
        self._anotar = anotar
        self.pedidos: list[Pedido] = []

    def __getattr__(self, nome):
        if nome not in OPERACOES_DO_COMPRADOR:
            raise AttributeError(f"o comprador não tem acesso a '{nome}'")
        operacao = getattr(self._borda, nome)

        def chamar(*args, **kwargs):
            conta = args[0] if args else kwargs.get("conta")
            if conta not in self._contas:
                raise ContaNaoEmitida(f"a conta '{conta}' não foi emitida para este participante")
            resposta = operacao(*args, **kwargs)
            if not self._anotar:
                return resposta
            argumentos = {"args": list(args), **kwargs}
            self.pedidos.append(Pedido(nome, argumentos, resposta))
            return resposta

        return chamar


class Participante(Protocol):
    """O que a rodada espera do bot de A2 (#10). A população A1 segue o mesmo formato."""

    def cadastrar(self, borda: BordaObservada, identidades: IdentidadesA2) -> None:
        """Cria as contas pedindo ids a ``identidades.nova_conta()`` e clusters a
        ``identidades.novo_cluster()``, e cadastra cada uma pela Borda."""

    def agir(self, tick: int, borda: BordaObservada) -> None:
        """Faz as requisições deste tick."""


@dataclass
class Abertura:
    """Tudo o que aconteceu numa abertura de vendas, antes de virar observação."""

    numero: int
    semente: int
    ticks: int
    plataforma: Plataforma
    telemetria: Telemetria
    identidades: Identidades
    populacao: list[CompradorA1]
    pedidos_a2: list[Pedido] = field(default_factory=list)


class _AgenteA1:
    """Adapta um CompradorA1 ao formato de participante."""

    def __init__(self, comprador: CompradorA1):
        self.comprador = comprador

    def agir(self, tick: int, borda) -> None:
        self.comprador.agir(tick, borda)


def executar_abertura(
    numero: int,
    politica: PoliticaA3,
    bot_a2: Participante | None,
    parametros: Parametros | None = None,
    semente: int | None = None,
    log: Log | None = None,
) -> Abertura:
    parametros = parametros or Parametros()
    semente = parametros.simulacao.semente if semente is None else semente
    ticks = parametros.simulacao.duracao_abertura

    plataforma, borda = criar_ambiente(parametros, politica, semente, log or Log(), rodada=numero)
    identidades = Identidades(semente)
    telemetria = Telemetria()

    populacao = criar_populacao(parametros, semente, identidades)
    borda_a1 = BordaObservada(borda, identidades.contas_de("A1"), anotar=False)  # A1 não precisa de observação
    for comprador in populacao:
        comprador.cadastrar(borda_a1)

    identidades_a2 = IdentidadesA2(identidades, parametros.simulacao.contas_a2_max)
    borda_a2 = BordaObservada(borda, identidades_a2.emitidas)
    participantes: list[tuple[Any, BordaObservada]] = [(_AgenteA1(c), borda_a1) for c in populacao]
    if bot_a2 is not None:
        bot_a2.cadastrar(borda_a2, identidades_a2)
        participantes.append((bot_a2, borda_a2))

    ordem = random.Random(f"ordem:{semente}")
    for tick in range(ticks):
        ordem.shuffle(participantes)  # intercala A1 e A2 numa ordem sorteada
        for participante, borda_dele in participantes:
            participante.agir(tick, borda_dele)
        plataforma.avancar()
        telemetria.amostrar(plataforma)

    telemetria.fechar(plataforma)
    plataforma.log.registrar("fim_abertura", quem="sistema", ticks=ticks)
    return Abertura(numero, semente, ticks, plataforma, telemetria, identidades, populacao, borda_a2.pedidos)
