"""Contratos: os tipos de dados que todos os módulos do grupo compartilham.

Se um módulo precisa conversar com outro (núcleo, simulação, A2, A3, orquestração,
relatório), ele usa os tipos deste arquivo. Mudanças aqui devem ser combinadas com o grupo.

Usamos Pydantic porque:
- o Agno aceita esses modelos como formato de saída do LLM (``output_schema``);
- eles viram JSON com uma linha (``model_dump_json``), o que facilita o log.

O tempo é sempre contado em "ticks": 1 tick = 1 segundo simulado.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Ingresso e reserva
# ---------------------------------------------------------------------------


class EstadoIngresso(StrEnum):
    """Um ingresso está sempre em exatamente um destes estados (INV1)."""

    DISPONIVEL = "DISPONIVEL"
    RESERVADO = "RESERVADO"
    OFERTADO_FILA = "OFERTADO_FILA"
    VENDIDO = "VENDIDO"


class Ingresso(BaseModel):
    id: int
    setor: str  # "premium" ou "pista"
    preco: float
    estado: EstadoIngresso = EstadoIngresso.DISPONIVEL
    reserva_id: str | None = None  # preenchido só quando RESERVADO
    dono: str | None = None  # preenchido só quando VENDIDO
    ofertado_para: str | None = None  # quem recebeu a oferta; None em OFERTADO_FILA = esperando a vez


class StatusReserva(StrEnum):
    ATIVA = "ATIVA"
    PAGA = "PAGA"
    EXPIRADA = "EXPIRADA"


class Reserva(BaseModel):
    id: str
    ingresso_id: int
    conta: str
    cluster: str
    criada_em: int  # tick
    expira_em: int  # tick
    status: StatusReserva = StatusReserva.ATIVA
    veio_da_fila: bool = False
    pagamento_iniciado: bool = False
    prorrogada: bool = False  # R4: só pode ser prorrogada uma vez
    custo_pre_autorizacao: float = 0.0  # R3: custo simulado (0 se R3 desligado)


# ---------------------------------------------------------------------------
# Resposta da Borda (é tudo o que o comprador consegue ver)
# ---------------------------------------------------------------------------


class Categoria(StrEnum):
    """Tipo de resposta que o comprador recebe.

    Com R6 desligado, a Borda usa as categorias específicas.
    Com R6 ligado, toda rejeição vira REJEITADA (só INDISPONIVEL continua aparecendo).
    """

    OK = "OK"
    INDISPONIVEL = "INDISPONIVEL"
    REJEITADA = "REJEITADA"
    # específicas (só com R6 desligado):
    LIMITE_REQUISICOES = "LIMITE_REQUISICOES"
    LIMITE_INGRESSOS = "LIMITE_INGRESSOS"
    LIMITE_RESERVAS = "LIMITE_RESERVAS"
    SEM_CARTAO = "SEM_CARTAO"
    ERRO = "ERRO"  # conta não cadastrada, reserva inexistente, pedido inválido...


class RespostaBorda(BaseModel):
    ok: bool
    codigo: int  # no estilo HTTP: 200, 201, 403, 409, 429...
    categoria: Categoria
    mensagem: str
    dados: dict[str, Any] = {}  # resultado da operação (reserva criada, lista de ingressos...)
    detalhe: dict[str, Any] = {}  # informação extra exposta, ex.: o limiar do 429
    tick: int


# ---------------------------------------------------------------------------
# Decisões dos agentes
# ---------------------------------------------------------------------------


class TipoEstrategiaA2(StrEnum):
    REGULAR = "REGULAR"
    INTENSIVO = "INTENSIVO"  # muitas requisições, poucas contas
    IMOBILIZACAO_RECAPTURA = "IMOBILIZACAO_RECAPTURA"  # reservar sem pagar e pegar de volta
    PULVERIZAR_CONTAS = "PULVERIZAR_CONTAS"  # muitas contas abaixo do limiar
    PAGAR_FRACAO = "PAGAR_FRACAO"  # pagar algumas para disfarçar
    OCUPAR_FILA = "OCUPAR_FILA"  # muitas posições na fila
    COMPRAR = "COMPRAR"  # comprar de verdade


class EstrategiaA2(BaseModel):
    """O que A2 decide no início de cada rodada (saída do agente A2, #10)."""

    tipo: TipoEstrategiaA2
    num_contas: int = Field(ge=1)
    clusters_distintos: int = Field(default=1, ge=1)  # 1 = todas as contas correlacionadas
    origens_distintas: int = Field(default=1, ge=1)  # quantos IPs diferentes
    requisicoes_por_minuto: int = Field(ge=1)
    fracao_pagamento: float = Field(default=1.0, ge=0.0, le=1.0)
    monitorar_disponibilidade: bool = False
    entrar_fila: bool = False
    justificativa: str = ""


class LimiteRequisicoes(BaseModel):
    ativo: bool = False
    maximo: int = Field(default=30, ge=1)  # requisições permitidas...
    janela: int = Field(default=60, ge=1)  # ...a cada tantos ticks
    por: str = Field(default="origem", pattern="^(origem|conta)$")


class R1(BaseModel):  # devolução pela fila
    ativo: bool = False
    prazo_oferta: int = Field(default=120, ge=1)


class R2(BaseModel):  # limite de reservas ativas
    ativo: bool = False
    max_por_conta: int = Field(default=1, ge=1)
    max_por_cluster: int = Field(default=1, ge=1)


class R3(BaseModel):  # pré-autorização
    ativo: bool = False
    custo: float = Field(default=10.0, ge=0.0)


class R4(BaseModel):  # prorrogação única
    ativo: bool = False
    prorrogacao: int = Field(default=300, ge=1)


class R5(BaseModel):  # rebaixamento na fila
    ativo: bool = False
    limiar_expiracoes: int = Field(default=2, ge=1)


class R6(BaseModel):  # mensagem genérica
    ativo: bool = False


class PoliticaA3(BaseModel):
    """O que A3 decide no início de cada rodada (saída do agente A3, #11).

    Os valores padrão são o estado inicial do 3.3 (D5): 4 ingressos por conta,
    TTL de 10 minutos e nenhum controle ligado.
    """

    limite_por_conta: int = Field(default=4, ge=1)
    ttl: int = Field(default=600, ge=1)  # 600 ticks = 10 minutos
    limite_requisicoes: LimiteRequisicoes = LimiteRequisicoes()
    r1: R1 = R1()
    r2: R2 = R2()
    r3: R3 = R3()
    r4: R4 = R4()
    r5: R5 = R5()
    r6: R6 = R6()
    justificativa: str = ""

    def controles_ligados(self) -> list[str]:
        nomes = []
        if self.limite_requisicoes.ativo:
            nomes.append("limite_requisicoes")
        for nome in ["r1", "r2", "r3", "r4", "r5", "r6"]:
            if getattr(self, nome).ativo:
                nomes.append(nome)
        return nomes


# ---------------------------------------------------------------------------
# Observações (o que cada agente enxerga no fim da rodada) e resultado
# ---------------------------------------------------------------------------


class ObservacaoA2(BaseModel):
    """Só o que A2 consegue ver pelas respostas da Borda. Nada interno da plataforma."""

    rodada: int
    estrategia: EstrategiaA2
    requisicoes: int = 0
    respostas_por_categoria: dict[str, int] = {}
    limiares_vistos: list[dict[str, Any]] = []  # ex.: o detalhe de um 429
    reservas_obtidas: int = 0
    reservas_expiradas: int = 0
    recapturas: int = 0
    ingressos_comprados: int = 0
    ofertas_da_fila: int = 0
    custo_pre_autorizacao: float = 0.0
    contas_canceladas: int = 0


class ObservacaoA3(BaseModel):
    """Telemetria e indicadores, sem saber quem é A1 e quem é A2."""

    rodada: int
    politica: PoliticaA3
    requisicoes: int = 0
    rejeicoes_por_motivo: dict[str, int] = {}
    reservas_criadas: int = 0
    reservas_pagas: int = 0
    reservas_expiradas: int = 0
    conversao: float = 0.0  # reservas pagas / reservas criadas
    conversao_por_cluster: dict[str, float] = {}
    conversao_por_conta: dict[str, float] = {}  # só contas que reservaram algo (ids opacos)
    estoque_retido: list[float] = []  # fração do lote RESERVADO ao longo da rodada
    periodicidade: int | None = None  # picos de devolução a cada N ticks, se houver
    vendidos: int = 0
    nao_vendidos: int = 0
    contas_marcadas: list[str] = []
    contas_rebaixadas: list[str] = []
    desistencias: int = 0
    contestacoes: int = 0


class Indicadores(BaseModel):
    """Verdade da rodada (quem é A1 e quem é A2). Só para a análise, nunca para os agentes."""

    ingressos_a1: int = 0
    ingressos_a2: int = 0
    premium_a1: int = 0  # dos ingressos acima, quantos são do setor premium
    premium_a2: int = 0
    estoque_retido_medio: float = 0.0
    conversao_a1: float = 0.0
    conversao_a2: float = 0.0
    desistencia_a1: int = 0
    falsos_positivos_a1: int = 0
    contestacoes: int = 0
    ganho_a2: float = 0.0


class ResultadoRodada(BaseModel):
    rodada: int
    semente: int
    politica: PoliticaA3
    estrategia: EstrategiaA2
    observacao_a2: ObservacaoA2
    observacao_a3: ObservacaoA3
    indicadores: Indicadores
    ticks: int


# ---------------------------------------------------------------------------
# Log: cada linha do arquivo .jsonl é um Evento
# ---------------------------------------------------------------------------


class Evento(BaseModel):
    """Uma linha do log JSONL.

    Não guardamos a hora real, só o tick. Assim, a mesma semente gera o mesmo log.
    Tipos usados pelo núcleo: politica, cadastro, requisicao, transicao, reserva,
    reserva_rejeitada, expiracao, prorrogacao, pagamento_iniciado, pagamento,
    fila_entrada, rebaixamento, oferta, oferta_respondida, oferta_vencida,
    repeticao, cancelamento. Os outros módulos podem criar tipos novos
    (por exemplo: decisao_a2, decisao_a3, resultado_rodada).
    """

    seq: int  # posição do evento no log (0, 1, 2...)
    rodada: int | None = None
    tick: int
    tipo: str
    quem: str | None = None  # conta, "A2", "A3" ou "sistema"
    dados: dict[str, Any] = {}
