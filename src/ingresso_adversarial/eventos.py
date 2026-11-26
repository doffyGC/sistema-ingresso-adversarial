"""Log de eventos: guarda tudo o que acontece e salva em JSONL (um JSON por linha)."""

from pathlib import Path

from .contratos import Evento


class Log:
    def __init__(self):
        self.eventos: list[Evento] = []
        self.rodada: int | None = None
        self.tick = 0  # quem usa o log atualiza o tick (a Plataforma faz isso)

    def registrar(self, tipo: str, quem: str | None = None, **dados) -> Evento:
        evento = Evento(
            seq=len(self.eventos),
            rodada=self.rodada,
            tick=self.tick,
            tipo=tipo,
            quem=quem,
            dados=dados,
        )
        self.eventos.append(evento)
        return evento

    def do_tipo(self, tipo: str) -> list[Evento]:
        return [e for e in self.eventos if e.tipo == tipo]

    def para_texto(self) -> str:
        linhas = [e.model_dump_json() for e in self.eventos]
        return "\n".join(linhas) + "\n"

    def salvar(self, arquivo) -> None:
        arquivo = Path(arquivo)
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text(self.para_texto(), encoding="utf-8")


def ler_log(arquivo) -> list[Evento]:
    linhas = Path(arquivo).read_text(encoding="utf-8").splitlines()
    return [Evento.model_validate_json(linha) for linha in linhas if linha]
