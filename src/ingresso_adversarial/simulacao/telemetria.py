"""Telemetria da rodada: o que a plataforma mede sobre requisições e transições (#9).

Tudo sai de duas fontes: uma amostra do estoque a cada tick e o log de eventos do núcleo.
A telemetria é o lado de A3: vê contas, clusters e o motivo exato de cada rejeição, mas não
sabe quem é A1 e quem é A2.
"""

from collections import Counter
from dataclasses import dataclass, field

from ..contratos import EstadoIngresso
from ..plataforma import Plataforma


@dataclass
class Telemetria:
    total_ingressos: int = 0
    retido: list[float] = field(default_factory=list)  # fração do lote RESERVADO, por tick
    disponiveis: list[int] = field(default_factory=list)  # ingressos em DISPONIVEL, por tick

    # Preenchidos por ``fechar`` a partir do log
    requisicoes: int = 0
    requisicoes_por_conta: Counter = field(default_factory=Counter)
    rejeicoes_por_motivo: Counter = field(default_factory=Counter)
    rejeicoes_por_conta: dict[str, Counter] = field(default_factory=dict)
    reservas_por_conta: Counter = field(default_factory=Counter)
    pagas_por_conta: Counter = field(default_factory=Counter)
    reservas_por_cluster: Counter = field(default_factory=Counter)
    pagas_por_cluster: Counter = field(default_factory=Counter)
    expiradas_por_conta: Counter = field(default_factory=Counter)
    ofertas_vencidas_por_conta: Counter = field(default_factory=Counter)
    devolucoes_por_tick: Counter = field(default_factory=Counter)  # voltas ao público
    devolucoes_por_ingresso: dict[int, list[int]] = field(default_factory=dict)  # ingresso -> ticks
    rebaixadas: list[str] = field(default_factory=list)
    canceladas: list[str] = field(default_factory=list)  # donos de vendas canceladas
    donos: dict[int, str] = field(default_factory=dict)  # ingresso vendido -> conta
    setores: dict[int, str] = field(default_factory=dict)  # ingresso -> setor

    def amostrar(self, plataforma: Plataforma) -> None:
        """Chamada depois de cada tick."""
        ingressos = plataforma.estoque.ingressos.values()
        self.total_ingressos = len(ingressos)
        reservados = sum(1 for i in ingressos if i.estado == EstadoIngresso.RESERVADO)
        self.retido.append(reservados / self.total_ingressos)
        self.disponiveis.append(sum(1 for i in ingressos if i.estado == EstadoIngresso.DISPONIVEL))

    def fechar(self, plataforma: Plataforma) -> "Telemetria":
        """Agrega o log no fim da rodada."""
        cluster_da_reserva = {}
        for evento in plataforma.log.eventos:
            d = evento.dados
            if evento.tipo == "requisicao":
                self.requisicoes += 1
                self.requisicoes_por_conta[evento.quem] += 1
                if d.get("motivo"):
                    self.rejeicoes_por_motivo[d["motivo"]] += 1
                    self.rejeicoes_por_conta.setdefault(evento.quem, Counter())[d["motivo"]] += 1
            elif evento.tipo == "reserva":
                self.reservas_por_conta[evento.quem] += 1
                self.reservas_por_cluster[d["cluster"]] += 1
                cluster_da_reserva[d["reserva"]] = d["cluster"]
            elif evento.tipo == "pagamento":
                self.pagas_por_conta[evento.quem] += 1
                self.pagas_por_cluster[cluster_da_reserva[d["reserva"]]] += 1
            elif evento.tipo == "expiracao":
                self.expiradas_por_conta[d["conta"]] += 1
            elif evento.tipo == "oferta_vencida":
                self.ofertas_vencidas_por_conta[d["conta"]] += 1
            elif evento.tipo == "volta_ao_publico":
                self.devolucoes_por_tick[evento.tick] += 1
                self.devolucoes_por_ingresso.setdefault(d["ingresso"], []).append(evento.tick)
            elif evento.tipo == "rebaixamento":
                self.rebaixadas.append(d["conta"])
            elif evento.tipo == "cancelamento":
                self.canceladas.append(d["dono"])

        for ingresso in plataforma.estoque.ingressos.values():
            self.setores[ingresso.id] = ingresso.setor
            if ingresso.estado == EstadoIngresso.VENDIDO:
                self.donos[ingresso.id] = ingresso.dono
        return self

    # ------------------------------------------------------------------
    # Medidas derivadas
    # ------------------------------------------------------------------

    @property
    def reservas_criadas(self) -> int:
        return sum(self.reservas_por_conta.values())

    @property
    def reservas_pagas(self) -> int:
        return sum(self.pagas_por_conta.values())

    @property
    def reservas_expiradas(self) -> int:
        return sum(self.expiradas_por_conta.values())

    @property
    def vendidos(self) -> int:
        return len(self.donos)

    def conversao_por_cluster(self) -> dict[str, float]:
        return {c: self.pagas_por_cluster[c] / n for c, n in sorted(self.reservas_por_cluster.items())}

    def retido_por_minuto(self) -> list[float]:
        """Série resumida (um ponto a cada 60 ticks) para caber na observação de A3."""
        return [round(max(self.retido[i : i + 60]), 3) for i in range(0, len(self.retido), 60)]

    def periodicidade(self) -> int | None:
        """De quantos em quantos ticks o mesmo ingresso volta ao público, se houver padrão.

        Na recaptura em ciclos (PE3), A2 reserva, deixa expirar e reserva de novo: cada
        ingresso volta ao público a cada ~TTL. Por isso o intervalo é medido entre as
        devoluções **do mesmo ingresso**; entre ticks seguidos, as rajadas de expiração
        dariam intervalos de 1 tick e esconderiam o ciclo.

        Devolve a mediana dos intervalos quando há pelo menos três e quando pelo menos
        metade deles fica a até 10% dela. Devoluções esparsas, como as de A1, dão None.
        """
        intervalos = sorted(
            b - a
            for ticks in self.devolucoes_por_ingresso.values()
            for a, b in zip(ticks, ticks[1:])
        )
        if len(intervalos) < 3:
            return None
        mediana = intervalos[len(intervalos) // 2]
        tolerancia = max(1, mediana // 10)
        perto = sum(1 for i in intervalos if abs(i - mediana) <= tolerancia)
        return mediana if perto * 2 >= len(intervalos) else None
