"""Critérios de aceite da issue #9."""

import inspect

import pytest
from bot_falso import BotRecaptura, intensivo, regular
from conftest import politica

from ingresso_adversarial import carregar_parametros
from ingresso_adversarial import plataforma as nucleo
from ingresso_adversarial.contratos import Categoria, EstadoIngresso
from ingresso_adversarial.eventos import Log
from ingresso_adversarial.simulacao import executar_abertura, executar_rodada, montar_resultado
from ingresso_adversarial.simulacao.observacoes import observacao_a2

PARAMETROS = carregar_parametros()


def rodada(bot, semente=42, pol=None, log=None):
    pol = pol or PARAMETROS.politica_inicial
    return executar_rodada(1, pol, bot.estrategia, bot, PARAMETROS, semente, log)


def test_criterio_intensivo_x_permitir_a2_fica_com_a_maior_parte_do_premium():
    """Sem controles, A2 intensivo captura a maior parte do setor premium.

    Com 10 contas e 4 ingressos por conta, A2 chega a no máximo 40 dos 100 ingressos.
    Por isso o critério é medido no que A2 quer revender: o premium.
    """
    indicadores = rodada(intensivo(num_contas=PARAMETROS.simulacao.contas_a2_max)).indicadores
    assert indicadores.premium_a2 > PARAMETROS.lote.premium / 2
    assert indicadores.premium_a2 > indicadores.premium_a1


def test_criterio_com_a2_regular_a1_fica_com_a_maior_parte_do_lote():
    indicadores = rodada(regular()).indicadores
    assert indicadores.ingressos_a1 > PARAMETROS.lote.quantidade / 2
    assert indicadores.ingressos_a1 > indicadores.ingressos_a2


def test_criterio_observacao_de_a2_nao_contem_dado_interno():
    abertura = executar_abertura(
        1, politica(r1={"ativo": True}, r2={"ativo": True}), intensivo(), PARAMETROS, 42
    )
    obs = montar_resultado(abertura, abertura.plataforma.politica, intensivo().estrategia).observacao_a2
    texto = obs.model_dump_json()

    # Nenhuma conta, cluster ou dono que A2 não controla.
    contas_a1 = abertura.identidades.contas_de("A1")
    clusters = {c.cluster for c in abertura.plataforma.contas.values()}
    assert not any(conta in texto for conta in contas_a1)
    assert not any(cluster in texto for cluster in clusters)
    # Nenhum motivo interno de rejeição (DA5) nem estado do estoque.
    # (LIMITE_REQUISICOES também é uma categoria pública: é o 429 que A2 recebe.)
    publicas = {c.value for c in Categoria}
    motivos = [v for n, v in vars(nucleo).items() if n.isupper() and type(v) is str and v not in publicas]
    assert motivos
    assert not any(f'"{motivo}"' in texto for motivo in motivos)
    assert not any(f'"{estado.value}"' in texto for estado in EstadoIngresso)
    # Por construção: a observação só recebe o que a Borda respondeu ao bot.
    assert list(inspect.signature(observacao_a2).parameters) == ["numero", "estrategia", "pedidos", "tick_final"]


def test_criterio_mesma_semente_mesmos_indicadores():
    primeiro_log, segundo_log = Log(), Log()
    primeiro = rodada(intensivo(), semente=42, log=primeiro_log)
    segundo = rodada(intensivo(), semente=42, log=segundo_log)
    assert primeiro == segundo
    assert primeiro_log.para_texto() == segundo_log.para_texto()
    assert rodada(intensivo(), semente=7) != primeiro


def test_observacao_de_a3_nao_separa_a1_de_a2():
    resultado = rodada(intensivo())
    texto = resultado.observacao_a3.model_dump_json().lower()
    assert "a1" not in texto and "a2" not in texto
    assert resultado.observacao_a3.vendidos == resultado.indicadores.ingressos_a1 + resultado.indicadores.ingressos_a2


def test_recaptura_sem_controles_aparece_na_telemetria():
    """Com R1 desligado (PE3), ingressos expirados voltam ao público e geram devoluções."""
    pol = politica(ttl=60)
    abertura = executar_abertura(1, pol, None, PARAMETROS, 42)
    assert sum(abertura.telemetria.devolucoes_por_tick.values()) > 0


@pytest.mark.parametrize("ttl", [120, 600])
def test_periodicidade_revela_a_recaptura_em_ciclos(ttl):
    """PE3: com R1 desligado, o bot de recaptura devolve cada ingresso a cada ~TTL."""
    bot = BotRecaptura()
    resultado = executar_rodada(1, politica(ttl=ttl), bot.estrategia, bot, PARAMETROS, 42)
    assert resultado.observacao_a3.periodicidade is not None
    assert abs(resultado.observacao_a3.periodicidade - ttl) <= ttl // 10


@pytest.mark.parametrize("semente", [1, 7, 42])
def test_sem_recaptura_nao_ha_periodicidade(semente):
    """A1 e um A2 que compra de verdade não deixam um ciclo de devoluções."""
    assert rodada(intensivo(), semente=semente, pol=politica(ttl=120)).observacao_a3.periodicidade is None
    assert rodada(regular(), semente=semente, pol=politica(ttl=120)).observacao_a3.periodicidade is None


def test_observacao_de_a3_traz_conversao_por_conta_e_por_cluster():
    """A recaptura aparece como contas e cluster com conversão zero, sem dizer que são de A2."""
    bot = BotRecaptura()
    abertura = executar_abertura(1, politica(), bot, PARAMETROS, 42)
    obs = montar_resultado(abertura, politica(), bot.estrategia).observacao_a3
    contas_a2 = abertura.identidades.contas_de("A2")
    assert contas_a2 <= set(obs.conversao_por_conta)
    assert all(obs.conversao_por_conta[c] == 0.0 for c in contas_a2)
    assert any(v > 0 for c, v in obs.conversao_por_conta.items() if c not in contas_a2)
    assert set(obs.conversao_por_cluster) <= {c.cluster for c in abertura.plataforma.contas.values()}
