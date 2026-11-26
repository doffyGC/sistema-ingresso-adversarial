"""Estoque: o ÚNICO lugar do código que muda o estado de um ingresso (DA2).

Reserva, expiração, fila e pagamento não mexem no ingresso diretamente: eles pedem
ao Estoque. O Estoque confere se a mudança está no diagrama de estados antes de fazer.
Se não estiver, nada muda e um erro é lançado.
"""

from .contratos import EstadoIngresso, Ingresso
from .eventos import Log

DISPONIVEL = EstadoIngresso.DISPONIVEL
RESERVADO = EstadoIngresso.RESERVADO
OFERTADO_FILA = EstadoIngresso.OFERTADO_FILA
VENDIDO = EstadoIngresso.VENDIDO

# Todas as mudanças de estado permitidas: (de, para).
TRANSICOES_PERMITIDAS = {
    (DISPONIVEL, RESERVADO),  # alguém reservou
    (RESERVADO, VENDIDO),  # pagou
    (RESERVADO, OFERTADO_FILA),  # expirou com R1 ligado: vai para a fila
    (RESERVADO, DISPONIVEL),  # expirou com R1 desligado (ou fila sem ninguém)
    (OFERTADO_FILA, RESERVADO),  # quem estava na fila aceitou
    (OFERTADO_FILA, OFERTADO_FILA),  # recusou, não respondeu ou esperava a vez: passa ao próximo
    (OFERTADO_FILA, DISPONIVEL),  # a fila acabou
    (VENDIDO, OFERTADO_FILA),  # cancelamento a posteriori (A3, #11)
    (VENDIDO, DISPONIVEL),  # cancelamento com a fila vazia
}


class TransicaoInvalida(Exception):
    pass


class Estoque:
    def __init__(self, ingressos: list[Ingresso], log: Log):
        self.ingressos = {ingresso.id: ingresso for ingresso in ingressos}
        self.log = log

    def estado(self, ingresso_id: int) -> EstadoIngresso:
        return self.ingressos[ingresso_id].estado

    def no_estado(self, estado: EstadoIngresso) -> list[Ingresso]:
        return [i for i in self.ingressos.values() if i.estado == estado]

    def mudar_estado(
        self,
        ingresso_id: int,
        novo: EstadoIngresso,
        motivo: str,
        reserva_id: str | None = None,
        dono: str | None = None,
        ofertado_para: str | None = None,
    ) -> None:
        ingresso = self.ingressos[ingresso_id]
        atual = ingresso.estado

        if (atual, novo) not in TRANSICOES_PERMITIDAS:
            raise TransicaoInvalida(f"ingresso {ingresso_id}: {atual} -> {novo} não é permitido")

        # Cada estado exige a informação que o descreve.
        if novo == RESERVADO and reserva_id is None:
            raise TransicaoInvalida("RESERVADO precisa da reserva")
        if novo == VENDIDO and dono is None:
            raise TransicaoInvalida("VENDIDO precisa do dono")
        # OFERTADO_FILA sem ofertado_para = o ingresso espera a vez na fila (DA1).

        # Só chega aqui se tudo estiver certo: agora muda de uma vez.
        ingresso.estado = novo
        ingresso.reserva_id = reserva_id
        ingresso.dono = dono
        ingresso.ofertado_para = ofertado_para

        self.log.registrar(
            "transicao",
            quem="sistema",
            ingresso=ingresso_id,
            de=atual.value,
            para=novo.value,
            motivo=motivo,
        )
