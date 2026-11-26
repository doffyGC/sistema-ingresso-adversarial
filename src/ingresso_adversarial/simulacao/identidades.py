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
