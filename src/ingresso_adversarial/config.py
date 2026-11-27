"""Lê os parâmetros iniciais do arquivo config/parametros.toml (D4)."""

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field

from .contratos import PoliticaA3

# config/parametros.toml fica duas pastas acima deste arquivo (src/ingresso_adversarial/).
ARQUIVO_PADRAO = Path(__file__).parent.parent.parent / "config" / "parametros.toml"


class Simulacao(BaseModel):
    semente: int = 42
    rodadas: int = 5
    duracao_abertura: int = 1800
    compradores_a1: int = 60
    contas_a2_max: int = 10


class Lote(BaseModel):
    quantidade: int = 100
    premium: int = 20
    preco_premium: float = 500.0
    preco_pista: float = 200.0


class PopulacaoA1(BaseModel):
    """Como os compradores legítimos (A1) se comportam (#9). Tempo em ticks."""

    fracao_sem_cartao: float = Field(default=0.15, ge=0.0, le=1.0)  # pesa quando R3 liga
    fracao_ansiosa: float = Field(default=0.2, ge=0.0, le=1.0)  # cadência alta: falso positivo (P3)
    cadencia_normal: int = Field(default=5, ge=1)  # ticks entre duas ações
    cadencia_ansiosa: int = Field(default=1, ge=1)
    chegada_max: int = Field(default=120, ge=0)  # chegam entre o tick 0 e este
    pagar_min: int = Field(default=30, ge=1)  # tempo que cada um leva para pagar
    pagar_max: int = Field(default=900, ge=1)  # acima do TTL = "prazo curto" para ele
    ingressos_min: int = Field(default=1, ge=1)
    ingressos_max: int = Field(default=2, ge=1)
    preferencia_premium: float = Field(default=0.5, ge=0.0, le=1.0)
    tentativas_antes_da_fila: int = Field(default=3, ge=1)
    aceita_oferta: float = Field(default=0.85, ge=0.0, le=1.0)
    # Desistência por atrito
    desistencia_fila: float = Field(default=0.3, ge=0.0, le=1.0)  # em vez de entrar na fila
    desistencia_prazo: float = Field(default=0.5, ge=0.0, le=1.0)  # a reserva expirou antes de pagar
    desistencia_verificacao: float = Field(default=0.7, ge=0.0, le=1.0)  # recusado pela pré-autorização (R3)


class Parametros(BaseModel):
    simulacao: Simulacao = Simulacao()
    lote: Lote = Lote()
    populacao_a1: PopulacaoA1 = PopulacaoA1()
    politica_inicial: PoliticaA3 = PoliticaA3()


def carregar_parametros(arquivo=ARQUIVO_PADRAO) -> Parametros:
    with open(arquivo, "rb") as f:
        dados = tomllib.load(f)
    return Parametros(**dados)
