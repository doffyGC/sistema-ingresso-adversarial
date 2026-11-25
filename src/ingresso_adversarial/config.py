"""Lê os parâmetros iniciais do arquivo config/parametros.toml (D4)."""

import tomllib
from pathlib import Path

from pydantic import BaseModel

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


class Parametros(BaseModel):
    simulacao: Simulacao = Simulacao()
    lote: Lote = Lote()
    politica_inicial: PoliticaA3 = PoliticaA3()


def carregar_parametros(arquivo=ARQUIVO_PADRAO) -> Parametros:
    with open(arquivo, "rb") as f:
        dados = tomllib.load(f)
    return Parametros(**dados)
