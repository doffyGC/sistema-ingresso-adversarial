"""Bot falso de A2, só para testar a simulação (#9).

O bot de verdade, com todo o repertório de estratégias, é da #10. Este aqui entende só o
necessário para os critérios de aceite da #9:

- INTENSIVO: muitas requisições, reserva o premium primeiro e paga na hora;
- REGULAR (ou qualquer outro tipo): uma conta, cadência humana, compra até o limite.

Segue o formato ``Participante`` da rodada e só usa a Borda que recebe.
"""

from ingresso_adversarial.contratos import Categoria, EstrategiaA2, TipoEstrategiaA2

LIMITES = {Categoria.LIMITE_INGRESSOS, Categoria.LIMITE_RESERVAS, Categoria.REJEITADA}


class BotFalso:
    def __init__(self, estrategia: EstrategiaA2):
        self.estrategia = estrategia
        self.contas: list[str] = []
        self.cheias: set[str] = set()  # contas que bateram em algum limite
        self.a_pagar: list[tuple[str, str]] = []  # (conta, reserva_id)
        self.vistos: list[dict] = []  # última lista de disponíveis
        self.orcamento = 0.0  # requisições acumuladas (requisicoes_por_minuto / 60 por tick)
        self.vez = 0

    def cadastrar(self, borda, identidades) -> None:
        e = self.estrategia
        clusters = [identidades.novo_cluster() for _ in range(e.clusters_distintos)]
        for n in range(e.num_contas):
            conta = identidades.nova_conta()
            borda.cadastrar(conta, clusters[n % len(clusters)])
            self.contas.append(conta)

    def origem(self) -> str:
        return f"o{self.vez % self.estrategia.origens_distintas}"

    def agir(self, tick: int, borda) -> None:
        self.orcamento += self.estrategia.requisicoes_por_minuto / 60
        while self.orcamento >= 1:
            self.orcamento -= 1
            self.vez += 1
            if not self.uma_requisicao(borda):
                self.orcamento = 0
                return

    def uma_requisicao(self, borda) -> bool:
        """Faz uma requisição. Devolve False quando não há mais o que fazer neste tick."""
        if self.a_pagar:
            conta, reserva_id = self.a_pagar.pop(0)
            borda.pagar(conta, reserva_id, chave=f"pg-{reserva_id}", origem=self.origem())
            return True

        livres = [c for c in self.contas if c not in self.cheias]
        if not livres:
            return False
        if not self.vistos:
            resposta = borda.ver_disponiveis(livres[0], origem=self.origem())
            self.vistos = resposta.dados.get("ingressos", []) if resposta.ok else []
            return bool(self.vistos)

        # Premium primeiro: é o que A2 revende com margem.
        self.vistos.sort(key=lambda i: (i["setor"] != "premium", i["id"]))
        ingresso = self.vistos.pop(0)
        conta = livres[self.vez % len(livres)]
        resposta = borda.reservar(conta, ingresso["id"], chave=f"r-{conta}-{self.vez}", origem=self.origem())
        if resposta.ok:
            if self.estrategia.fracao_pagamento > 0:
                self.a_pagar.append((conta, resposta.dados["reserva_id"]))
        elif resposta.categoria in LIMITES:
            self.cheias.add(conta)
        return True


def intensivo(num_contas=10, rpm=600) -> BotFalso:
    return BotFalso(EstrategiaA2(tipo=TipoEstrategiaA2.INTENSIVO, num_contas=num_contas, requisicoes_por_minuto=rpm))


def regular() -> BotFalso:
    return BotFalso(EstrategiaA2(tipo=TipoEstrategiaA2.REGULAR, num_contas=1, requisicoes_por_minuto=6))
