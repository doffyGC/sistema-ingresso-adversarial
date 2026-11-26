"""Protótipo do sistema adversarial de venda de ingressos (Trabalho 2)."""

from .borda import Borda
from .config import Parametros, carregar_parametros
from .contratos import PoliticaA3
from .eventos import Log
from .plataforma import Plataforma


def criar_ambiente(parametros=None, politica=None, semente=None, log=None, rodada=None):
    """Cria uma rodada nova (uma abertura de vendas): a Plataforma e a Borda que a expõe."""
    plataforma = Plataforma(parametros, politica, semente, log, rodada)
    return plataforma, Borda(plataforma)
