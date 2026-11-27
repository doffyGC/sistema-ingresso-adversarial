"""Simulação de uma abertura de vendas: população A1, rodada, telemetria e observações (#9).

Uso pela orquestração (#12)::

    from ingresso_adversarial.simulacao import executar_rodada

    resultado = executar_rodada(1, politica, estrategia, bot_a2, parametros, semente=42)
    resultado.observacao_a2   # vai para o agente A2
    resultado.observacao_a3   # vai para o agente A3
    resultado.indicadores     # só para a análise
"""

from ..config import Parametros
from ..contratos import EstrategiaA2, PoliticaA3, ResultadoRodada
from ..eventos import Log
from .identidades import Identidades, IdentidadesA2, LimiteDeContasA2
from .indicadores import calcular_indicadores
from .observacoes import observacao_a2, observacao_a3
from .rodada import Abertura, BordaObservada, ContaNaoEmitida, Participante, Pedido, executar_abertura

__all__ = [
    "Abertura",
    "BordaObservada",
    "ContaNaoEmitida",
    "Identidades",
    "IdentidadesA2",
    "LimiteDeContasA2",
    "Participante",
    "Pedido",
    "executar_abertura",
    "executar_rodada",
    "montar_resultado",
]


def montar_resultado(abertura: Abertura, politica: PoliticaA3, estrategia: EstrategiaA2) -> ResultadoRodada:
    telemetria = abertura.telemetria
    return ResultadoRodada(
        rodada=abertura.numero,
        semente=abertura.semente,
        politica=politica,
        estrategia=estrategia,
        observacao_a2=observacao_a2(abertura.numero, estrategia, abertura.pedidos_a2, abertura.ticks),
        observacao_a3=observacao_a3(abertura.numero, politica, telemetria),
        indicadores=calcular_indicadores(
            telemetria,
            abertura.identidades.contas_de("A1"),
            abertura.identidades.contas_de("A2"),
            abertura.populacao,
        ),
        ticks=abertura.ticks,
    )


def executar_rodada(
    numero: int,
    politica: PoliticaA3,
    estrategia: EstrategiaA2,
    bot_a2: Participante | None,
    parametros: Parametros | None = None,
    semente: int | None = None,
    log: Log | None = None,
) -> ResultadoRodada:
    """Executa uma abertura de vendas e devolve as observações e os indicadores."""
    abertura = executar_abertura(numero, politica, bot_a2, parametros, semente, log)
    return montar_resultado(abertura, politica, estrategia)
