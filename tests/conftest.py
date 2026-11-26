"""Funções de apoio usadas por todos os testes."""

import random

from ingresso_adversarial import Parametros, PoliticaA3, criar_ambiente
from ingresso_adversarial.config import Lote


def politica(**mudancas):
    """Política do estado inicial com algumas mudanças.

    Exemplo: politica(ttl=60, r1={"ativo": True}) liga o R1 e muda o TTL para 60.
    """
    dados = PoliticaA3().model_dump()
    for nome, valor in mudancas.items():
        if isinstance(valor, dict):
            dados[nome].update(valor)
        else:
            dados[nome] = valor
    return PoliticaA3(**dados)


def ambiente(pol=None, ingressos=10, semente=42):
    """Cria uma rodada pequena (10 ingressos) para os testes ficarem rápidos."""
    parametros = Parametros(lote=Lote(quantidade=ingressos, premium=2))
    return criar_ambiente(parametros, pol or PoliticaA3(), semente)


def cadastrar(borda, *contas, cluster=None, tem_cartao=True):
    for conta in contas:
        resposta = borda.cadastrar(conta, cluster or f"cluster-{conta}", tem_cartao)
        assert resposta.ok


def compradores_aleatorios(plataforma, borda, semente, ticks, depois_de_cada_tick=None):
    """12 compradores fazendo ações sorteadas pela Borda.

    Não é a população A1 (#9): serve só para testar que as regras valem
    "não importa o que os agentes decidam".
    """
    sorteio = random.Random(semente)
    contas = [f"c{n}" for n in range(12)]
    for n, conta in enumerate(contas):
        borda.cadastrar(conta, cluster=f"cl{n % 3}", tem_cartao=(n % 5 != 0))
    chaves = []  # (conta, chave, ingresso) já usadas, para testar repetições
    total_ingressos = len(plataforma.estoque.ingressos)

    for _ in range(ticks):
        for conta in contas:
            acao = sorteio.random()
            origem = f"ip{sorteio.randint(1, 4)}"
            minhas = [r for r in plataforma.reservas_ativas() if r.conta == conta]

            if acao < 0.25:
                borda.ver_disponiveis(conta, origem)
            elif acao < 0.40:
                ingresso = sorteio.randint(1, total_ingressos)
                chave = f"k{sorteio.randint(0, 10**9)}"
                chaves.append((conta, chave, ingresso))
                borda.reservar(conta, ingresso, chave, origem)
            elif acao < 0.50 and chaves:
                c, chave, ingresso = sorteio.choice(chaves)  # repete uma requisição antiga
                borda.reservar(c, ingresso, chave, origem)
            elif acao < 0.58 and minhas:
                borda.iniciar_pagamento(conta, sorteio.choice(minhas).id, origem=origem)
            elif acao < 0.60 and minhas:
                reserva = sorteio.choice(minhas)
                borda.pagar(conta, reserva.id, f"pg-{reserva.id}", origem)
                borda.pagar(conta, reserva.id, f"pg-{reserva.id}", origem)  # repetição
            elif acao < 0.72:
                borda.entrar_fila(conta, origem)
            elif acao < 0.85:
                oferta = borda.consultar_fila(conta, origem).dados.get("oferta")
                if oferta:
                    aceitar = sorteio.random() < 0.6
                    borda.responder_oferta(conta, oferta["ingresso_id"], aceitar, origem=origem)

        plataforma.avancar()
        if depois_de_cada_tick:
            depois_de_cada_tick()
