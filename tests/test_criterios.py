"""Critérios de aceite da issue #8."""

from conftest import ambiente, cadastrar, compradores_aleatorios, politica

from ingresso_adversarial.contratos import Categoria, EstadoIngresso


def test_criterio_1_cem_tentativas_no_mesmo_tick_criam_uma_reserva():
    plataforma, borda = ambiente()
    contas = [f"c{n}" for n in range(100)]
    cadastrar(borda, *contas)
    respostas = [borda.reservar(conta, 1) for conta in contas]  # todas no tick 0
    assert len([r for r in respostas if r.ok]) == 1
    assert len([r for r in respostas if r.categoria == Categoria.INDISPONIVEL]) == 99
    assert len(plataforma.reservas) == 1


def test_criterio_2_mesma_chave_mesmo_resultado_sem_novo_efeito():
    plataforma, borda = ambiente()
    cadastrar(borda, "ana")
    primeira = borda.reservar("ana", 1, chave="abc")
    plataforma.avancar(3)
    segunda = borda.reservar("ana", 1, chave="abc")
    assert primeira.ok
    assert segunda == primeira
    assert len(plataforma.reservas) == 1


def test_criterio_3_expirado_nao_reaparece_enquanto_ha_fila():
    plataforma, borda = ambiente(politica(ttl=5, r1={"ativo": True, "prazo_oferta": 3}))
    cadastrar(borda, "a2", "monitor", "f1", "f2", "f3")
    for conta in ["f1", "f2", "f3"]:
        borda.entrar_fila(conta)
    borda.reservar("a2", 1)

    apareceu_com_fila = False
    for _ in range(20):
        plataforma.avancar()
        vistos = [i["id"] for i in borda.ver_disponiveis("monitor").dados["ingressos"]]
        if 1 in vistos and len(plataforma.fila) > 0:
            apareceu_com_fila = True
        # f2 recusa quando recebe a oferta; f1 e f3 deixam vencer.
        oferta = borda.consultar_fila("f2").dados["oferta"]
        if oferta:
            borda.responder_oferta("f2", oferta["ingresso_id"], aceitar=False)

    assert not apareceu_com_fila
    # Quando a fila acaba, o ingresso volta a circular.
    assert plataforma.estoque.estado(1) == EstadoIngresso.DISPONIVEL
    assert sorted(e.dados["conta"] for e in plataforma.log.do_tipo("oferta")) == ["f1", "f2", "f3"]


def expirar_em_massa(contas_na_fila, reservas=3):
    """A2 reserva varios ingressos e deixa todos expirarem no mesmo tick."""
    plataforma, borda = ambiente(politica(ttl=5, r1={"ativo": True, "prazo_oferta": 4}))
    cadastrar(borda, "a2", "monitor", *contas_na_fila)
    for conta in contas_na_fila:
        borda.entrar_fila(conta)
    ingressos = list(range(1, reservas + 1))
    for ingresso in ingressos:
        assert borda.reservar("a2", ingresso).ok
    plataforma.avancar(5)  # todas expiram juntas
    return plataforma, borda, ingressos


def visiveis(borda, ingressos):
    lista = borda.ver_disponiveis("monitor").dados["ingressos"]
    return [i["id"] for i in lista if i["id"] in ingressos]


def test_criterio_3_expiracoes_simultaneas_esperam_a_vez_na_fila():
    """Tres reservas expiram juntas e so ha uma conta na fila: nenhuma volta ao publico."""
    plataforma, borda, ingressos = expirar_em_massa(["f1"])

    estados = [plataforma.estoque.estado(i) for i in ingressos]
    assert estados == [EstadoIngresso.OFERTADO_FILA] * 3
    assert visiveis(borda, ingressos) == []
    # A2 nao consegue recapturar enquanto f1 esta na fila.
    assert all(not borda.reservar("a2", i).ok for i in ingressos)

    oferta = borda.consultar_fila("f1").dados["oferta"]
    assert borda.responder_oferta("f1", oferta["ingresso_id"], aceitar=True).ok
    # f1 saiu da fila: agora a fila acabou e os outros dois voltam ao publico.
    assert sorted(visiveis(borda, ingressos)) == sorted(set(ingressos) - {oferta["ingresso_id"]})
    assert plataforma.verificar_invariantes() == []


def test_criterio_3_expiracoes_simultaneas_com_fila_que_nao_responde():
    """Duas contas na fila deixam as ofertas vencerem: os ingressos so voltam no fim da fila."""
    plataforma, borda, ingressos = expirar_em_massa(["f1", "f2"])
    problemas = []
    for _ in range(20):
        if len(plataforma.fila) > 0:
            assert visiveis(borda, ingressos) == []
        problemas.extend(plataforma.verificar_invariantes())
        plataforma.avancar()

    assert problemas == []
    assert len(plataforma.fila) == 0
    assert sorted(visiveis(borda, ingressos)) == ingressos


def test_desligar_r1_devolve_ao_publico_os_ingressos_em_espera():
    plataforma, borda, ingressos = expirar_em_massa(["f1"])
    ofertado = borda.consultar_fila("f1").dados["oferta"]["ingresso_id"]
    em_espera = sorted(set(ingressos) - {ofertado})

    plataforma.aplicar_politica(politica(ttl=5, r1={"ativo": False}))
    assert sorted(visiveis(borda, ingressos)) == em_espera
    # A oferta que já estava aberta continua valendo até o prazo dela.
    assert plataforma.estoque.estado(ofertado) == EstadoIngresso.OFERTADO_FILA
    assert plataforma.verificar_invariantes() == []


def test_criterio_3_quem_aceita_a_oferta_fica_com_o_ingresso():
    plataforma, borda = ambiente(politica(ttl=5, r1={"ativo": True}))
    cadastrar(borda, "a2", "a1")
    borda.entrar_fila("a1")
    borda.reservar("a2", 1)
    plataforma.avancar(5)
    aceite = borda.responder_oferta("a1", 1, aceitar=True)
    assert aceite.ok
    assert borda.pagar("a1", aceite.dados["reserva_id"]).ok
    assert plataforma.estoque.ingressos[1].dono == "a1"


def test_criterio_4_segunda_reserva_do_cluster_sem_revelar_o_limiar():
    plataforma, borda = ambiente(politica(r2={"ativo": True}))
    cadastrar(borda, "x1", "x2", cluster="X")
    assert borda.reservar("x1", 1).ok

    pelo_cluster = borda.reservar("x2", 2)  # dispara o limite do cluster
    pela_conta = borda.reservar("x1", 3)  # dispara o limite da conta
    assert pelo_cluster.categoria == Categoria.LIMITE_RESERVAS
    assert pelo_cluster == pela_conta  # resposta idêntica: não dá para saber qual foi
    assert pelo_cluster.detalhe == {}
    assert "cluster" not in pelo_cluster.mensagem.lower()
    assert not any(c.isdigit() for c in pelo_cluster.mensagem)
    # No log interno o motivo exato aparece (DA5).
    motivos = [e.dados["motivo"] for e in plataforma.log.do_tipo("reserva_rejeitada")]
    assert motivos == ["R2_LIMITE_CLUSTER", "R2_LIMITE_CONTA"]


def test_criterio_4_com_r6_vira_a_resposta_generica():
    plataforma, borda = ambiente(politica(r2={"ativo": True}, r3={"ativo": True}, r6={"ativo": True}))
    cadastrar(borda, "x1", "x2", cluster="X")
    cadastrar(borda, "sem_cartao", tem_cartao=False)
    borda.reservar("x1", 1)
    pelo_cluster = borda.reservar("x2", 2)
    sem_cartao = borda.reservar("sem_cartao", 3)
    assert pelo_cluster.categoria == Categoria.REJEITADA
    assert pelo_cluster == sem_cartao


def test_recaptura_pe3_funciona_com_tudo_desligado():
    """O ataque da rodada 1 precisa ser possível no estado inicial."""
    plataforma, borda = ambiente()  # TTL de 600 e nenhum controle
    cadastrar(borda, "a2", "a1")
    borda.entrar_fila("a1")  # a fila existe, mas sem R1 ela não recebe a devolução
    reserva = borda.reservar("a2", 1)
    assert reserva.dados["expira_em"] == 600

    plataforma.avancar(599)
    assert 1 not in [i["id"] for i in borda.ver_disponiveis("a2").dados["ingressos"]]
    plataforma.avancar(1)  # tick 600: expira e volta ao público
    assert 1 in [i["id"] for i in borda.ver_disponiveis("a2").dados["ingressos"]]
    assert borda.reservar("a2", 1).ok  # A2 pega de novo no mesmo tick
    assert [r.conta for r in plataforma.reservas.values()] == ["a2", "a2"]


def rodar(semente):
    plataforma, borda = ambiente(politica(ttl=12, r1={"ativo": True, "prazo_oferta": 4}, r4={"ativo": True}, r5={"ativo": True}), ingressos=8, semente=semente)
    compradores_aleatorios(plataforma, borda, semente, ticks=150)
    return plataforma.log.para_texto()


def test_mesma_semente_mesmo_resultado():
    assert rodar(42) == rodar(42)


def test_semente_diferente_muda_a_ordem_da_fila():
    def ordem(semente):
        plataforma, borda = ambiente(semente=semente)
        contas = [f"c{n}" for n in range(20)]
        cadastrar(borda, *contas)
        for conta in contas:
            borda.entrar_fila(conta)
        return plataforma.fila.ordem()

    assert ordem(1) == ordem(1)
    assert ordem(1) != ordem(2)
