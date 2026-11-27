"""Identidades opacas das contas e dos clusters de uma rodada.

A3 vê ids de conta e de cluster na telemetria, mas não pode saber quem é A1 e quem é A2.
Por isso os ids são sorteados (``c4821``, ``k0917``) e não carregam o lado. Só a rodada
guarda o dono de cada conta, para calcular os indicadores de análise.
"""

import random


class Identidades:
    def __init__(self, semente: int):
        self.sorteio = random.Random(f"identidades:{semente}")
        self.dono: dict[str, str] = {}  # conta -> "A1" ou "A2" (verdade da rodada)
        self.usados: set[str] = set()

    def _novo(self, prefixo: str) -> str:
        while True:
            candidato = f"{prefixo}{self.sorteio.randrange(10**5):05d}"
            if candidato not in self.usados:
                self.usados.add(candidato)
                return candidato

    def nova_conta(self, dono: str) -> str:
        conta = self._novo("c")
        self.dono[conta] = dono
        return conta

    def novo_cluster(self) -> str:
        return self._novo("k")

    def contas_de(self, dono: str) -> set[str]:
        return {conta for conta, quem in self.dono.items() if quem == dono}


class LimiteDeContasA2(Exception):
    """A2 pediu mais contas do que a rodada permite (``contas_a2_max``, D4)."""


class IdentidadesA2:
    """O que o bot de A2 recebe: só criar contas e clusters.

    Não dá acesso ao dono das outras contas, então o bot não descobre quem é A1.
    Toda conta criada por aqui fica registrada como de A2, e o ambiente só aceita
    requisições do bot com as contas emitidas aqui, até ``maximo`` contas.
    """

    def __init__(self, identidades: Identidades, maximo: int):
        self._identidades = identidades
        self.maximo = maximo
        self.emitidas: set[str] = set()

    def nova_conta(self) -> str:
        if len(self.emitidas) >= self.maximo:
            raise LimiteDeContasA2(f"A2 pode ter no máximo {self.maximo} contas")
        conta = self._identidades.nova_conta("A2")
        self.emitidas.add(conta)
        return conta

    def novo_cluster(self) -> str:
        return self._identidades.novo_cluster()
