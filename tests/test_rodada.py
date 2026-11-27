"""Execução de uma abertura de vendas (#9)."""

import pytest
from bot_falso import intensivo, regular
from conftest import politica

from ingresso_adversarial import carregar_parametros
from ingresso_adversarial.contratos import RespostaBorda
from ingresso_adversarial.simulacao import (
    BordaObservada,
    ContaNaoEmitida,
    IdentidadesA2,
    LimiteDeContasA2,
    executar_abertura,
)

POLITICAS = {
    "estado inicial": politica(),
    "R1 e R2": politica(r1={"ativo": True}, r2={"ativo": True}),
    "todos ligados": politica(
        limite_requisicoes={"ativo": True},
        r1={"ativo": True},
        r2={"ativo": True},
        r3={"ativo": True},
        r4={"ativo": True},
        r5={"ativo": True},
        r6={"ativo": True},
    ),
}


@pytest.mark.parametrize("nome", POLITICAS)
def test_invariantes_valem_ao_fim_da_rodada(nome):
    parametros = carregar_parametros()
    abertura = executar_abertura(1, POLITICAS[nome], intensivo(), parametros, 42)
    assert abertura.plataforma.verificar_invariantes() == []
    assert abertura.telemetria.vendidos <= parametros.lote.quantidade
    assert len(abertura.telemetria.retido) == parametros.simulacao.duracao_abertura


def test_participante_so_recebe_as_operacoes_do_comprador():
    recebidas = []

    class Espiao:
        def cadastrar(self, borda, identidades):
            recebidas.append(borda)
            recebidas.append(identidades)
            borda.cadastrar(identidades.nova_conta(), identidades.novo_cluster())

        def agir(self, tick, borda):
            recebidas.append(borda)

    executar_abertura(1, politica(), Espiao(), carregar_parametros(), 42)
    bordas = [b for b in recebidas if not isinstance(b, IdentidadesA2)]
    assert all(isinstance(b, BordaObservada) for b in bordas)
    # As identidades do bot só criam contas: não dizem quem é dono de quê.
    identidades = next(r for r in recebidas if isinstance(r, IdentidadesA2))
    assert not hasattr(identidades, "dono") and not hasattr(identidades, "contas_de")
    with pytest.raises(AttributeError):
        bordas[0].plataforma  # não alcança o estoque por trás da Borda
    with pytest.raises(AttributeError):
        bordas[0].traduzir


def test_pedidos_do_bot_guardam_so_respostas_da_borda():
    abertura = executar_abertura(1, politica(), regular(), carregar_parametros(), 42)
    assert abertura.pedidos_a2
    assert all(isinstance(p.resposta, RespostaBorda) for p in abertura.pedidos_a2)


def test_a1_e_a2_se_intercalam_no_mesmo_tick():
    abertura = executar_abertura(1, politica(), intensivo(), carregar_parametros(), 42)
    contas_a2 = abertura.identidades.contas_de("A2")
    quem_no_tick_0 = [
        e.quem in contas_a2
        for e in abertura.plataforma.log.do_tipo("requisicao")
        if e.tick == 0 and e.dados["operacao"] != "cadastrar"
    ]
    # Há requisições dos dois lados, e a ordem não é "todos de um lado, depois o outro".
    trocas = sum(1 for a, b in zip(quem_no_tick_0, quem_no_tick_0[1:]) if a != b)
    assert True in quem_no_tick_0 and False in quem_no_tick_0
    assert trocas >= 1


def test_a2_nao_passa_do_limite_de_contas():
    """D4: A2 tem no máximo contas_a2_max contas; o ambiente impõe, não o bot."""
    parametros = carregar_parametros()
    maximo = parametros.simulacao.contas_a2_max
    with pytest.raises(LimiteDeContasA2):
        executar_abertura(1, politica(), intensivo(num_contas=maximo + 1), parametros, 42)
    abertura = executar_abertura(1, politica(), intensivo(num_contas=maximo), parametros, 42)
    assert len(abertura.identidades.contas_de("A2")) == maximo


class BotComIdsProprios:
    def __init__(self, conta):
        self.conta = conta

    def cadastrar(self, borda, identidades):
        borda.cadastrar(self.conta, identidades.novo_cluster())

    def agir(self, tick, borda):
        pass


def test_bot_so_age_com_contas_emitidas_pelo_ambiente():
    """Um id inventado pelo bot não entraria em ingressos_a2 e vazaria na ObservacaoA3."""
    with pytest.raises(ContaNaoEmitida):
        executar_abertura(1, politica(), BotComIdsProprios("bot0"), carregar_parametros(), 42)


def test_bot_nao_age_em_nome_de_conta_de_a1():
    parametros = carregar_parametros()
    conta_de_a1 = next(iter(executar_abertura(1, politica(), None, parametros, 42).identidades.contas_de("A1")))
    with pytest.raises(ContaNaoEmitida):
        executar_abertura(1, politica(), BotComIdsProprios(conta_de_a1), parametros, 42)
