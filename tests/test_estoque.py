"""DA2: só o Estoque muda o estado, e só pelas transições do diagrama."""

import pytest

from ingresso_adversarial.contratos import EstadoIngresso, Ingresso
from ingresso_adversarial.estoque import Estoque, TransicaoInvalida
from ingresso_adversarial.eventos import Log


def novo_estoque():
    return Estoque([Ingresso(id=1, setor="pista", preco=200.0)], Log())


def test_reservar_e_vender():
    estoque = novo_estoque()
    estoque.mudar_estado(1, EstadoIngresso.RESERVADO, "teste", reserva_id="R1")
    estoque.mudar_estado(1, EstadoIngresso.VENDIDO, "teste", dono="ana")
    assert estoque.estado(1) == EstadoIngresso.VENDIDO
    assert estoque.ingressos[1].dono == "ana"
    assert estoque.ingressos[1].reserva_id is None


def test_nao_pula_direto_para_vendido():
    estoque = novo_estoque()
    with pytest.raises(TransicaoInvalida):
        estoque.mudar_estado(1, EstadoIngresso.VENDIDO, "teste", dono="ana")
    assert estoque.estado(1) == EstadoIngresso.DISPONIVEL


def test_nao_reserva_duas_vezes():
    estoque = novo_estoque()
    estoque.mudar_estado(1, EstadoIngresso.RESERVADO, "teste", reserva_id="R1")
    with pytest.raises(TransicaoInvalida):
        estoque.mudar_estado(1, EstadoIngresso.RESERVADO, "teste", reserva_id="R2")
    assert estoque.ingressos[1].reserva_id == "R1"


def test_reservado_precisa_da_reserva():
    estoque = novo_estoque()
    with pytest.raises(TransicaoInvalida):
        estoque.mudar_estado(1, EstadoIngresso.RESERVADO, "teste")
    assert estoque.estado(1) == EstadoIngresso.DISPONIVEL
