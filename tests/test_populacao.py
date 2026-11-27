"""População A1 (#9): variação controlada pela semente."""

import pytest
from bot_falso import intensivo, regular
from conftest import politica

from ingresso_adversarial import carregar_parametros
from ingresso_adversarial.simulacao import Identidades, executar_abertura
from ingresso_adversarial.simulacao.populacao import criar_populacao


def perfis(semente):
    parametros = carregar_parametros()
    populacao = criar_populacao(parametros, semente, Identidades(semente))
    return [(c.conta, c.tem_cartao, c.ansioso, c.chegada, c.tempo_pagar, c.quantidade) for c in populacao]


def test_mesma_semente_mesma_populacao():
    assert perfis(42) == perfis(42)
    assert perfis(42) != perfis(7)


def test_fracoes_da_populacao_seguem_os_parametros():
    parametros = carregar_parametros()
    populacao = criar_populacao(parametros, 42, Identidades(42))
    total = parametros.simulacao.compradores_a1
    assert len(populacao) == total
    assert sum(not c.tem_cartao for c in populacao) == round(total * parametros.populacao_a1.fracao_sem_cartao)
    assert sum(c.ansioso for c in populacao) == round(total * parametros.populacao_a1.fracao_ansiosa)
    # Parte da população demora mais que o TTL para pagar ("prazo curto").
    assert any(c.tempo_pagar > parametros.politica_inicial.ttl for c in populacao)


def test_ids_nao_revelam_quem_e_a1():
    parametros = carregar_parametros()
    identidades = Identidades(42)
    populacao = criar_populacao(parametros, 42, identidades)
    for comprador in populacao:
        assert "a1" not in comprador.conta.lower() and "a1" not in comprador.cluster.lower()
    assert identidades.contas_de("A1") == {c.conta for c in populacao}


def test_sem_a2_a1_compra_sem_ser_barrado():
    parametros = carregar_parametros()
    abertura = executar_abertura(1, parametros.politica_inicial, None, parametros, 42)
    compradores = abertura.populacao
    assert sum(c.comprados for c in compradores) == abertura.telemetria.vendidos > 50
    assert abertura.plataforma.verificar_invariantes() == []


def test_ansioso_leva_429_quando_a3_liga_o_limite_de_requisicoes():
    """Falso positivo (P3): o comprador legítimo e ansioso esbarra no limite."""
    parametros = carregar_parametros()
    pol = politica(limite_requisicoes={"ativo": True, "maximo": 30, "janela": 60, "por": "conta"})
    abertura = executar_abertura(1, pol, None, parametros, 42)
    barrados = {
        conta
        for conta, motivos in abertura.telemetria.rejeicoes_por_conta.items()
        if "LIMITE_REQUISICOES" in motivos
    }
    ansiosos = {c.conta for c in abertura.populacao if c.ansioso}
    assert barrados and barrados <= ansiosos


def test_recusar_a_oferta_tem_motivo_proprio():
    """Quem recusa a oferta da fila não se confunde com quem desistiu de entrar nela."""
    parametros = carregar_parametros()
    parametros.populacao_a1.aceita_oferta = 0.0  # todo mundo recusa
    abertura = executar_abertura(1, politica(r1={"ativo": True}), intensivo(), parametros, 42)
    recusaram = {e.quem for e in abertura.plataforma.log.do_tipo("oferta_respondida") if not e.dados["aceitou"]}
    motivos = {c.conta: c.desistiu for c in abertura.populacao}
    assert recusaram
    recusaram_a1 = recusaram & set(motivos)
    assert recusaram_a1 and all(motivos[conta] == "oferta" for conta in recusaram_a1)
    assert any(motivo == "fila" for motivo in motivos.values())  # o outro atrito continua separado


def test_sem_cartao_desiste_com_a_pre_autorizacao():
    parametros = carregar_parametros()
    abertura = executar_abertura(1, politica(r3={"ativo": True}), None, parametros, 42)
    desistentes = {c.conta for c in abertura.populacao if c.desistiu == "verificacao"}
    sem_cartao = {c.conta for c in abertura.populacao if not c.tem_cartao}
    assert desistentes and desistentes <= sem_cartao


@pytest.mark.parametrize("r6", [False, True])
@pytest.mark.parametrize("semente", [1, 42])
def test_429_no_pagamento_nao_faz_a1_perder_a_reserva(r6, semente):
    """Um 429 barra a requisição, não a reserva: A1 insiste e não perde a compra por isso.

    Com R6, o 429 chega como REJEITADA genérica, e o comprador insiste enquanto o prazo
    que recebeu ao reservar não passou. O log guarda o motivo exato para o teste conferir.
    """
    pol = politica(limite_requisicoes={"ativo": True, "por": "conta"}, r6={"ativo": r6})
    abertura = executar_abertura(1, pol, regular(), carregar_parametros(), semente)
    log = abertura.plataforma.log
    contas_a1 = abertura.identidades.contas_de("A1")

    barrados_no_pagamento = [
        (e.quem, e.tick)
        for e in log.do_tipo("requisicao")
        if e.quem in contas_a1 and e.dados["operacao"] == "pagar" and e.dados["motivo"] == "LIMITE_REQUISICOES"
    ]
    assert barrados_no_pagamento  # o cenário de fato aconteceu

    criada_em = {e.dados["reserva"]: e.tick for e in log.do_tipo("reserva")}
    for expiracao in log.do_tipo("expiracao"):
        conta, reserva = expiracao.dados["conta"], expiracao.dados["reserva"]
        if conta not in contas_a1:
            continue
        # Nenhuma reserva de A1 expira depois de um 429 no pagamento enquanto ela estava ativa.
        assert not any(
            quem == conta and criada_em[reserva] <= tick < expiracao.tick for quem, tick in barrados_no_pagamento
        ), f"a reserva {reserva} expirou depois de um 429 no pagamento"
    assert abertura.plataforma.verificar_invariantes() == []
