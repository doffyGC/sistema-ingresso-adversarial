"""População A1 (#9): variação controlada pela semente."""

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


def test_sem_cartao_desiste_com_a_pre_autorizacao():
    parametros = carregar_parametros()
    abertura = executar_abertura(1, politica(r3={"ativo": True}), None, parametros, 42)
    desistentes = {c.conta for c in abertura.populacao if c.desistiu == "verificacao"}
    sem_cartao = {c.conta for c in abertura.populacao if not c.tem_cartao}
    assert desistentes and desistentes <= sem_cartao
