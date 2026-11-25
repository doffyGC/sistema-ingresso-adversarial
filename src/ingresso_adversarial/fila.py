"""Fila de espera: ordem sorteada e rebaixamento para o fim (R5)."""

import random


class Fila:
    def __init__(self, sorteio: random.Random):
        self.sorteio = sorteio  # gerador com semente: mesma semente, mesma ordem
        self.numero = {}  # conta -> número sorteado na entrada (menor = mais na frente)
        self.rebaixadas = set()  # contas que foram para o fim da fila

    def __contains__(self, conta: str) -> bool:
        return conta in self.numero

    def __len__(self) -> int:
        return len(self.numero)

    def entrar(self, conta: str) -> None:
        self.numero[conta] = self.sorteio.random()

    def sair(self, conta: str) -> None:
        self.numero.pop(conta, None)
        self.rebaixadas.discard(conta)

    def rebaixar(self, conta: str) -> bool:
        """Manda a conta para o fim. Ela não sai da fila nem é bloqueada."""
        if conta not in self.numero or conta in self.rebaixadas:
            return False
        self.rebaixadas.add(conta)
        return True

    def ordem(self) -> list[str]:
        # Primeiro as não rebaixadas (False vem antes de True), depois pelo número sorteado.
        return sorted(self.numero, key=lambda conta: (conta in self.rebaixadas, self.numero[conta]))

    def posicao(self, conta: str) -> int | None:
        if conta not in self.numero:
            return None
        return self.ordem().index(conta) + 1
