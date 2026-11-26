"""Parâmetros iniciais (D4, D5), contratos e formato do log."""

import pytest
from pydantic import ValidationError

from ingresso_adversarial import Plataforma, carregar_parametros
from ingresso_adversarial.contratos import EstrategiaA2, PoliticaA3
from ingresso_adversarial.eventos import ler_log


def test_parametros_do_arquivo():
    parametros = carregar_parametros()
    assert parametros.lote.quantidade == 100
    assert parametros.simulacao.compradores_a1 == 60
    assert parametros.simulacao.contas_a2_max == 10
    assert parametros.simulacao.rodadas == 5


def test_parametros_da_populacao_a1():
    populacao = carregar_parametros().populacao_a1
    assert 0 < populacao.fracao_sem_cartao < 1
    assert 0 < populacao.fracao_ansiosa < 1
    assert populacao.cadencia_ansiosa < populacao.cadencia_normal
    # Parte de A1 demora mais que o TTL inicial para pagar: é o atrito do "prazo curto".
    assert populacao.pagar_min < carregar_parametros().politica_inicial.ttl < populacao.pagar_max


def test_politica_inicial_e_o_estado_inicial_do_3_3():
    inicial = carregar_parametros().politica_inicial
    assert inicial.limite_por_conta == 4
    assert inicial.ttl == 600
    assert inicial.controles_ligados() == []


def test_plataforma_funciona_no_estado_inicial():
    plataforma = Plataforma(carregar_parametros())
    assert len(plataforma.disponibilidade()) == 100
    assert plataforma.verificar_invariantes() == []


def test_estrategia_invalida_e_rejeitada():
    with pytest.raises(ValidationError):
        EstrategiaA2(tipo="NAO_EXISTE", num_contas=1, requisicoes_por_minuto=1)
    with pytest.raises(ValidationError):
        EstrategiaA2(tipo="REGULAR", num_contas=0, requisicoes_por_minuto=1)


def test_politica_invalida_e_rejeitada():
    with pytest.raises(ValidationError):
        PoliticaA3(ttl=0)
    with pytest.raises(ValidationError):
        PoliticaA3(limite_requisicoes={"por": "cpf"})


def test_politicas_nao_compartilham_os_controles():
    a = PoliticaA3()
    b = PoliticaA3()
    a.r1.ativo = True
    assert b.r1.ativo is False


def test_log_salva_e_le_jsonl(tmp_path):
    plataforma = Plataforma()
    plataforma.reservar("ninguem", 1)
    arquivo = tmp_path / "log.jsonl"
    plataforma.log.salvar(arquivo)
    assert ler_log(arquivo) == plataforma.log.eventos
