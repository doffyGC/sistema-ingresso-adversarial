"""Invariantes INV1 a INV6 (docs/decisoes-arquitetura.md)."""

import pytest
from conftest import ambiente, cadastrar, compradores_aleatorios, politica

from ingresso_adversarial.contratos import EstadoIngresso

POLITICAS = {
    "estado inicial": politica(ttl=20),
    "todos ligados": politica(
        ttl=20,
        limite_requisicoes={"ativo": True, "maximo": 8, "janela": 5},
        r1={"ativo": True, "prazo_oferta": 6},
        r2={"ativo": True},
        r3={"ativo": True},
        r4={"ativo": True, "prorrogacao": 10},
        r5={"ativo": True},
        r6={"ativo": True},
    ),
    "R1 e R2": politica(ttl=15, r1={"ativo": True, "prazo_oferta": 4}, r2={"ativo": True, "max_por_cluster": 2}),
    "R4 e R5": politica(ttl=10, r4={"ativo": True, "prorrogacao": 5}, r5={"ativo": True, "limiar_expiracoes": 1}),
}


@pytest.mark.parametrize("nome", POLITICAS)
@pytest.mark.parametrize("semente", [1, 7, 42])
def test_invariantes_valem_com_compradores_aleatorios(nome, semente):
    """300 ticks de ações sorteadas, conferindo os invariantes depois de cada tick."""
    plataforma, borda = ambiente(POLITICAS[nome], ingressos=8, semente=semente)
    problemas = []

    def conferir():
        problemas.extend(plataforma.verificar_invariantes())

    compradores_aleatorios(plataforma, borda, semente, ticks=300, depois_de_cada_tick=conferir)
    assert problemas == []


def test_inv1_cada_ingresso_tem_um_estado():
    plataforma, borda = ambiente()
    cadastrar(borda, "ana", "bia")
    borda.reservar("ana", 1)
    reserva = borda.reservar("bia", 2)
    borda.pagar("bia", reserva.dados["reserva_id"])
    estados = [i.estado for i in plataforma.estoque.ingressos.values()]
    assert estados.count(EstadoIngresso.DISPONIVEL) == 8
    assert estados.count(EstadoIngresso.RESERVADO) == 1
    assert estados.count(EstadoIngresso.VENDIDO) == 1
    assert plataforma.verificar_invariantes() == []


def test_inv2_so_uma_reserva_por_ingresso():
    plataforma, borda = ambiente()
    contas = [f"c{n}" for n in range(50)]
    cadastrar(borda, *contas)
    for conta in contas:
        borda.reservar(conta, 1)
    reservas_do_1 = [r for r in plataforma.reservas_ativas() if r.ingresso_id == 1]
    assert len(reservas_do_1) == 1


def test_inv3_limite_do_cluster_e_repeticao_sem_efeito():
    plataforma, borda = ambiente(politica(r2={"ativo": True}))
    cadastrar(borda, "x1", "x2", cluster="X")
    primeira = borda.reservar("x1", 1, chave="k1")
    segunda = borda.reservar("x2", 2, chave="k2")
    assert primeira.ok and not segunda.ok
    # Repetir a requisição rejeitada dá a mesma resposta e não cria nada.
    assert borda.reservar("x2", 2, chave="k2") == segunda
    assert len(plataforma.reservas_ativas()) == 1


def test_inv4_expirado_vai_para_a_fila_antes_do_publico():
    plataforma, borda = ambiente(politica(ttl=5, r1={"ativo": True}))
    cadastrar(borda, "a2", "a1")
    borda.entrar_fila("a1")
    borda.reservar("a2", 1)
    plataforma.avancar(5)
    assert plataforma.estoque.estado(1) == EstadoIngresso.OFERTADO_FILA
    assert plataforma.estoque.ingressos[1].ofertado_para == "a1"
    assert 1 not in [i.id for i in plataforma.disponibilidade()]


def test_inv5_ingresso_nao_fica_preso_na_fila():
    prazo = 4
    plataforma, borda = ambiente(politica(ttl=5, r1={"ativo": True, "prazo_oferta": prazo}))
    fila = [f"f{n}" for n in range(6)]
    cadastrar(borda, "a2", *fila)
    for conta in fila:
        borda.entrar_fila(conta)
    borda.reservar("a2", 1)
    plataforma.avancar(5)
    # Ninguém responde: cada oferta vence e passa ao próximo, até a fila acabar.
    plataforma.avancar(len(fila) * prazo)
    assert plataforma.estoque.estado(1) == EstadoIngresso.DISPONIVEL
    assert len(plataforma.fila) == 0


def test_inv6_repetir_pagamento_nao_cobra_de_novo():
    plataforma, borda = ambiente()
    cadastrar(borda, "ana")
    reserva_id = borda.reservar("ana", 1).dados["reserva_id"]
    primeira = borda.pagar("ana", reserva_id, chave="p1")
    segunda = borda.pagar("ana", reserva_id, chave="p1")
    assert primeira.ok and segunda == primeira
    assert plataforma.cobrancas == [reserva_id]
    # Sem a chave, a regra também impede: a reserva já foi paga.
    assert not borda.pagar("ana", reserva_id).ok
    assert plataforma.cobrancas == [reserva_id]


def test_verificacao_encontra_problema_de_verdade():
    """Garante que os testes acima não passam só porque a verificação nunca reclama."""
    plataforma, borda = ambiente()
    cadastrar(borda, "ana")
    borda.reservar("ana", 1)
    plataforma.reservas.clear()  # estraga o estado de propósito
    assert plataforma.verificar_invariantes() != []
