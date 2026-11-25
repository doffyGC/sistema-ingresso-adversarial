"""Controles que A3 pode ligar, desligar e ajustar: limite de requisições e R1 a R6."""

from conftest import ambiente, cadastrar, politica

from ingresso_adversarial.borda import MENSAGEM_GENERICA
from ingresso_adversarial.contratos import Categoria, EstadoIngresso

# ---- limite de requisições ----


def test_429_mostra_o_limiar_como_na_rodada_1():
    plataforma, borda = ambiente()
    cadastrar(borda, "bot1", "bot2")
    plataforma.aplicar_politica(politica(limite_requisicoes={"ativo": True, "maximo": 3, "janela": 10}))
    for _ in range(3):
        assert borda.ver_disponiveis("bot1", origem="ip-A").ok
    # Outra conta no mesmo IP conta para o mesmo limite.
    bloqueada = borda.ver_disponiveis("bot2", origem="ip-A")
    assert bloqueada.codigo == 429
    assert bloqueada.detalhe == {"maximo": 3, "janela": 10, "por": "origem"}
    assert "3" in bloqueada.mensagem
    # Outro IP passa; e depois da janela o IP volta a ser atendido.
    assert borda.ver_disponiveis("bot2", origem="ip-B").ok
    plataforma.avancar(10)
    assert borda.ver_disponiveis("bot1", origem="ip-A").ok


def test_limite_por_conta_ignora_o_ip():
    plataforma, borda = ambiente()
    cadastrar(borda, "ana", "bia")
    plataforma.aplicar_politica(politica(limite_requisicoes={"ativo": True, "maximo": 1, "por": "conta"}))
    assert borda.ver_disponiveis("ana", origem="ip").ok
    assert borda.ver_disponiveis("bia", origem="ip").ok
    assert borda.ver_disponiveis("ana", origem="outro-ip").codigo == 429


def test_429_com_r6_vira_resposta_generica():
    plataforma, borda = ambiente()
    cadastrar(borda, "ana")
    plataforma.aplicar_politica(politica(limite_requisicoes={"ativo": True, "maximo": 1}, r6={"ativo": True}))
    borda.ver_disponiveis("ana")
    bloqueada = borda.ver_disponiveis("ana")
    assert bloqueada.categoria == Categoria.REJEITADA
    assert bloqueada.mensagem == MENSAGEM_GENERICA
    assert bloqueada.detalhe == {}


def test_429_nao_fica_guardado_como_resposta_da_chave():
    plataforma, borda = ambiente()
    cadastrar(borda, "ana")
    plataforma.aplicar_politica(politica(limite_requisicoes={"ativo": True, "maximo": 1, "janela": 5}))
    borda.ver_disponiveis("ana")
    assert borda.reservar("ana", 1, chave="k").codigo == 429
    plataforma.avancar(5)
    assert borda.reservar("ana", 1, chave="k").ok


def test_sem_limite_nao_bloqueia():
    plataforma, borda = ambiente()
    cadastrar(borda, "ana")
    respostas = [borda.ver_disponiveis("ana") for _ in range(500)]
    assert all(r.ok for r in respostas)


# ---- limite de 4 por conta ----


def test_limite_de_4_ingressos_por_conta():
    plataforma, borda = ambiente()
    cadastrar(borda, "ana")
    for ingresso in [1, 2, 3, 4]:
        assert borda.reservar("ana", ingresso).ok
    quinta = borda.reservar("ana", 5)
    assert quinta.categoria == Categoria.LIMITE_INGRESSOS
    assert quinta.detalhe == {"limite_por_conta": 4}
    # Ingresso comprado também conta.
    borda.pagar("ana", plataforma.reservas_ativas()[0].id)
    assert not borda.reservar("ana", 5).ok


# ---- R1 ----


def test_r1_desligado_devolve_ao_publico_mesmo_com_fila():
    plataforma, borda = ambiente(politica(ttl=3))
    cadastrar(borda, "a2", "a1")
    borda.entrar_fila("a1")
    borda.reservar("a2", 1)
    plataforma.avancar(3)
    assert plataforma.estoque.estado(1) == EstadoIngresso.DISPONIVEL


def test_r1_ligado_com_fila_vazia_devolve_ao_publico():
    plataforma, borda = ambiente(politica(ttl=3, r1={"ativo": True}))
    cadastrar(borda, "a2")
    borda.reservar("a2", 1)
    plataforma.avancar(3)
    assert plataforma.estoque.estado(1) == EstadoIngresso.DISPONIVEL


def test_r1_pula_quem_ja_atingiu_o_limite():
    plataforma, borda = ambiente(politica(ttl=3, limite_por_conta=1, r1={"ativo": True}))
    cadastrar(borda, "a2", "cheio", "livre")
    borda.entrar_fila("cheio")
    borda.entrar_fila("livre")
    reserva = borda.reservar("cheio", 2)
    borda.pagar("cheio", reserva.dados["reserva_id"])  # "cheio" já tem 1 ingresso
    borda.reservar("a2", 1)
    plataforma.avancar(3)
    assert plataforma.estoque.ingressos[1].ofertado_para == "livre"


# ---- R2 ----


def test_r2_libera_nova_reserva_quando_a_anterior_acaba():
    plataforma, borda = ambiente(politica(ttl=3, r2={"ativo": True}))
    cadastrar(borda, "ana")
    assert borda.reservar("ana", 1).ok
    assert not borda.reservar("ana", 2).ok
    plataforma.avancar(3)
    assert borda.reservar("ana", 2).ok


def test_r2_desligado_permite_varias_reservas_do_cluster():
    plataforma, borda = ambiente()
    cadastrar(borda, "x1", "x2", "x3", cluster="X")
    assert borda.reservar("x1", 1).ok
    assert borda.reservar("x2", 2).ok
    assert borda.reservar("x3", 3).ok


# ---- R3 ----


def test_r3_cobra_pre_autorizacao_e_recusa_quem_nao_tem_cartao():
    plataforma, borda = ambiente(politica(r3={"ativo": True, "custo": 15.0}))
    cadastrar(borda, "com")
    cadastrar(borda, "sem", tem_cartao=False)
    assert borda.reservar("com", 1).dados["custo_pre_autorizacao"] == 15.0
    recusada = borda.reservar("sem", 2)
    assert recusada.codigo == 402
    assert recusada.categoria == Categoria.SEM_CARTAO


def test_r3_desligado_nao_cobra():
    plataforma, borda = ambiente()
    cadastrar(borda, "sem", tem_cartao=False)
    assert borda.reservar("sem", 1).dados["custo_pre_autorizacao"] == 0.0


# ---- R4 ----


def tick_em_que_expira(pol, iniciar_pagamento):
    plataforma, borda = ambiente(pol)
    cadastrar(borda, "ana")
    reserva_id = borda.reservar("ana", 1).dados["reserva_id"]
    if iniciar_pagamento:
        borda.iniciar_pagamento("ana", reserva_id)
    while plataforma.estoque.estado(1) == EstadoIngresso.RESERVADO:
        plataforma.avancar()
    return plataforma.tick


def test_r4_prorroga_uma_vez_se_o_pagamento_comecou():
    pol = politica(ttl=10, r4={"ativo": True, "prorrogacao": 5})
    assert tick_em_que_expira(pol, iniciar_pagamento=True) == 15
    assert tick_em_que_expira(pol, iniciar_pagamento=False) == 10


def test_r4_desligado_nao_prorroga():
    assert tick_em_que_expira(politica(ttl=10), iniciar_pagamento=True) == 10


def test_r4_da_tempo_de_pagar_depois_do_ttl():
    plataforma, borda = ambiente(politica(ttl=10, r4={"ativo": True, "prorrogacao": 5}))
    cadastrar(borda, "ana")
    reserva_id = borda.reservar("ana", 1).dados["reserva_id"]
    borda.iniciar_pagamento("ana", reserva_id)
    plataforma.avancar(12)
    assert borda.pagar("ana", reserva_id).ok


# ---- R5 ----


def deixar_expirar(plataforma, borda, conta, vezes, ttl):
    for _ in range(vezes):
        livre = plataforma.disponibilidade()[0].id
        assert borda.reservar(conta, livre).ok
        plataforma.avancar(ttl)


def test_r5_manda_para_o_fim_quem_deixa_expirar_varias_vezes():
    plataforma, borda = ambiente(politica(ttl=2, r5={"ativo": True, "limiar_expiracoes": 2}))
    outros = [f"c{n}" for n in range(8)]
    cadastrar(borda, "a2", *outros)
    deixar_expirar(plataforma, borda, "a2", vezes=2, ttl=2)
    borda.entrar_fila("a2")
    for conta in outros:
        borda.entrar_fila(conta)
    assert plataforma.fila.ordem()[-1] == "a2"
    # Perde a vez na fila, mas não é bloqueada: ainda pode reservar.
    assert borda.reservar("a2", plataforma.disponibilidade()[0].id).ok


def test_r5_rebaixa_quem_ja_esta_na_fila():
    plataforma, borda = ambiente(politica(ttl=2, r5={"ativo": True, "limiar_expiracoes": 1}))
    cadastrar(borda, "a2", "b", "c")
    for conta in ["a2", "b", "c"]:
        borda.entrar_fila(conta)
    deixar_expirar(plataforma, borda, "a2", vezes=1, ttl=2)
    assert plataforma.fila.ordem()[-1] == "a2"


def test_r5_desligado_nao_rebaixa():
    plataforma, borda = ambiente(politica(ttl=2))
    cadastrar(borda, "a2")
    deixar_expirar(plataforma, borda, "a2", vezes=3, ttl=2)
    borda.entrar_fila("a2")
    assert "a2" not in plataforma.fila.rebaixadas


def test_r5_ligado_no_meio_da_rodada():
    plataforma, borda = ambiente(politica(ttl=2))
    cadastrar(borda, "a2", "b")
    deixar_expirar(plataforma, borda, "a2", vezes=2, ttl=2)
    borda.entrar_fila("a2")
    borda.entrar_fila("b")
    plataforma.aplicar_politica(politica(ttl=2, r5={"ativo": True}))
    assert plataforma.fila.ordem() == ["b", "a2"]


# ---- R6 ----


def test_r6_ainda_mostra_ingresso_indisponivel():
    plataforma, borda = ambiente(politica(r6={"ativo": True}))
    cadastrar(borda, "ana", "bia")
    borda.reservar("ana", 1)
    assert borda.reservar("bia", 1).categoria == Categoria.INDISPONIVEL


def test_r6_conta_desconhecida_recebe_a_generica():
    plataforma, borda = ambiente(politica(r6={"ativo": True}))
    assert borda.reservar("desconhecida", 1).categoria == Categoria.REJEITADA


# ---- política nova vale para as próximas reservas ----


def test_politica_nova_vale_para_as_proximas_reservas():
    plataforma, borda = ambiente()
    cadastrar(borda, "ana")
    antes = borda.reservar("ana", 1)
    plataforma.aplicar_politica(politica(ttl=60))
    depois = borda.reservar("ana", 2)
    assert antes.dados["expira_em"] == 600
    assert depois.dados["expira_em"] == 60


# ---- cancelamento a posteriori (mecânica para #11) ----


def test_cancelamento_guarda_evidencia_e_oferece_a_fila():
    plataforma, borda = ambiente(politica(r1={"ativo": True}))
    cadastrar(borda, "a2", "a1")
    reserva_id = borda.reservar("a2", 1).dados["reserva_id"]
    borda.pagar("a2", reserva_id)
    borda.entrar_fila("a1")
    assert plataforma.cancelar_venda(1, "cluster confirmado", {"cluster": "X"})
    assert plataforma.estoque.ingressos[1].ofertado_para == "a1"
    assert plataforma.log.do_tipo("cancelamento")[0].dados["evidencia"] == {"cluster": "X"}
    assert plataforma.verificar_invariantes() == []
