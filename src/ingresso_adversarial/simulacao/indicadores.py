"""Indicadores da rodada: a verdade sobre quem é A1 e quem é A2 (#9).

Servem para a análise (#13) e para o relatório. **Nunca** vão para os agentes: A2 só vê a
``ObservacaoA2`` e A3 só vê a ``ObservacaoA3``.
"""

from ..contratos import Indicadores
from .. import plataforma as p
from .populacao import CompradorA1
from .telemetria import Telemetria

# Rejeições causadas por um controle de defesa. Quando atingem A1, são falso positivo.
MOTIVOS_DE_DEFESA = {p.LIMITE_REQUISICOES, p.R2_LIMITE_CONTA, p.R2_LIMITE_CLUSTER, p.R3_SEM_CARTAO}


def _conversao(telemetria: Telemetria, contas: set[str]) -> float:
    reservas = sum(telemetria.reservas_por_conta[c] for c in contas)
    pagas = sum(telemetria.pagas_por_conta[c] for c in contas)
    return round(pagas / reservas, 4) if reservas else 0.0


def contas_a1_atingidas(telemetria: Telemetria, contas_a1: set[str]) -> set[str]:
    """Contas A1 barradas por algum controle, rebaixadas na fila ou com venda cancelada."""
    atingidas = set()
    for conta in contas_a1:
        motivos = telemetria.rejeicoes_por_conta.get(conta, {})
        if any(m in MOTIVOS_DE_DEFESA for m in motivos):
            atingidas.add(conta)
    atingidas |= contas_a1 & set(telemetria.rebaixadas)
    atingidas |= contas_a1 & set(telemetria.canceladas)
    return atingidas


def calcular_indicadores(
    telemetria: Telemetria,
    contas_a1: set[str],
    contas_a2: set[str],
    populacao: list[CompradorA1],
) -> Indicadores:
    def vendidos_para(contas, setor=None):
        return sum(
            1
            for ingresso, dono in telemetria.donos.items()
            if dono in contas and (setor is None or telemetria.setores[ingresso] == setor)
        )

    retido = telemetria.retido
    return Indicadores(
        ingressos_a1=vendidos_para(contas_a1),
        ingressos_a2=vendidos_para(contas_a2),
        premium_a1=vendidos_para(contas_a1, "premium"),
        premium_a2=vendidos_para(contas_a2, "premium"),
        estoque_retido_medio=round(sum(retido) / len(retido), 4) if retido else 0.0,
        conversao_a1=_conversao(telemetria, contas_a1),
        conversao_a2=_conversao(telemetria, contas_a2),
        desistencia_a1=sum(1 for c in populacao if c.desistiu is not None),
        falsos_positivos_a1=len(contas_a1_atingidas(telemetria, contas_a1)),
        contestacoes=0,  # ainda não há caminho de contestação no núcleo (#11, INV7)
        ganho_a2=0.0,  # a avaliação do ponto de vista de A2 é da #10
    )
