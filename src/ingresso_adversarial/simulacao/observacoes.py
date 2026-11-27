"""O que cada lado consegue observar no fim da rodada (#9).

A assimetria do T1 ("f2 = f4"): os dois lados olham a mesma interação por janelas diferentes.

- **A2** só sabe o que a Borda respondeu a ele. ``observacao_a2`` recebe apenas a lista de
  pedidos e respostas do bot; não tem como enxergar o estoque, as outras contas ou o motivo
  interno de uma rejeição.
- **A3** vê a telemetria agregada da plataforma (contas, clusters, motivos), mas não sabe
  quem é A1 e quem é A2: os ids são opacos e nada aqui usa o dono das contas.
"""

import json
from collections import Counter

from ..contratos import EstrategiaA2, ObservacaoA2, ObservacaoA3, PoliticaA3
from .rodada import Pedido
from .telemetria import Telemetria

OPERACOES_QUE_RESERVAM = {"reservar", "responder_oferta"}


def observacao_a2(numero: int, estrategia: EstrategiaA2, pedidos: list[Pedido], tick_final: int) -> ObservacaoA2:
    categorias = Counter()
    limiares = {}
    reservas = {}  # reserva_id -> {"ingresso", "expira_em"}
    pagas = set()
    recapturas = 0
    ofertas = set()
    custo = 0.0

    for pedido in pedidos:
        resposta = pedido.resposta
        categorias[resposta.categoria.value] += 1
        if resposta.detalhe:
            limiares[json.dumps(resposta.detalhe, sort_keys=True)] = resposta.detalhe

        dados = resposta.dados
        if not resposta.ok:
            continue
        reserva_id = dados.get("reserva_id")

        if pedido.operacao in OPERACOES_QUE_RESERVAM and reserva_id and reserva_id not in reservas:
            ingresso = dados["ingresso_id"]
            # Recaptura: A2 volta a reservar um ingresso que já foi dele e não foi pago.
            if any(r["ingresso"] == ingresso and rid not in pagas for rid, r in reservas.items()):
                recapturas += 1
            reservas[reserva_id] = {"ingresso": ingresso, "expira_em": dados["expira_em"]}
            custo += dados.get("custo_pre_autorizacao", 0.0)
        elif pedido.operacao == "pagar" and reserva_id:
            pagas.add(reserva_id)
        elif reserva_id in reservas and "expira_em" in dados:
            reservas[reserva_id]["expira_em"] = dados["expira_em"]  # prazo visto mais recente (R4)
        elif pedido.operacao == "consultar_fila" and dados.get("oferta"):
            ofertas.add(dados["oferta"]["ingresso_id"])

    expiradas = [rid for rid, r in reservas.items() if rid not in pagas and r["expira_em"] <= tick_final]
    return ObservacaoA2(
        rodada=numero,
        estrategia=estrategia,
        requisicoes=len(pedidos),
        respostas_por_categoria=dict(sorted(categorias.items())),
        limiares_vistos=list(limiares.values()),
        reservas_obtidas=len(reservas),
        reservas_expiradas=len(expiradas),
        recapturas=recapturas,
        ingressos_comprados=len(pagas),
        ofertas_da_fila=len(ofertas),
        custo_pre_autorizacao=custo,
        contas_canceladas=0,  # A2 ainda não recebe aviso de cancelamento pela Borda
    )


def observacao_a3(numero: int, politica: PoliticaA3, telemetria: Telemetria) -> ObservacaoA3:
    criadas = telemetria.reservas_criadas
    desistentes = {
        conta
        for conta in set(telemetria.expiradas_por_conta) | set(telemetria.ofertas_vencidas_por_conta)
        if telemetria.pagas_por_conta[conta] == 0
    }
    return ObservacaoA3(
        rodada=numero,
        politica=politica,
        requisicoes=telemetria.requisicoes,
        rejeicoes_por_motivo=dict(sorted(telemetria.rejeicoes_por_motivo.items())),
        reservas_criadas=criadas,
        reservas_pagas=telemetria.reservas_pagas,
        reservas_expiradas=telemetria.reservas_expiradas,
        conversao=round(telemetria.reservas_pagas / criadas, 4) if criadas else 0.0,
        conversao_por_cluster={c: round(v, 4) for c, v in telemetria.conversao_por_cluster().items()},
        conversao_por_conta={c: round(v, 4) for c, v in telemetria.conversao_por_conta().items()},
        estoque_retido=telemetria.retido_por_minuto(),
        periodicidade=telemetria.periodicidade(),
        vendidos=telemetria.vendidos,
        nao_vendidos=telemetria.total_ingressos - telemetria.vendidos,
        contas_marcadas=[],  # quem marca é o Detector de A3 (#11)
        contas_rebaixadas=sorted(set(telemetria.rebaixadas)),
        desistencias=len(desistentes),
        contestacoes=0,
    )
