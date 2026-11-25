# Núcleo do ambiente (T2)

O núcleo é o "mundo" em que os agentes agem: o ciclo de vida do ingresso descrito em
[`resiliencia.md`](resiliencia.md), seguindo os invariantes INV1–INV6 de
[`decisoes-arquitetura.md`](decisoes-arquitetura.md). Ele não toma decisões de agente e
não usa LLM. Com a mesma semente, o resultado é sempre o mesmo.

## Como rodar os testes

```bash
uv sync
uv run pytest
```

## Arquivos (`src/ingresso_adversarial/`)

| Arquivo | O que faz |
|---|---|
| `contratos.py` | Tipos que todos os módulos do grupo usam, inclusive o formato do log (`Evento`) |
| `config.py` | Lê `config/parametros.toml` (D4) e a política inicial de A3 (D5) |
| `eventos.py` | Log de eventos, salvo em JSONL |
| `estoque.py` | **Único** lugar que muda o estado de um ingresso (DA2) |
| `fila.py` | Fila de espera sorteada pela semente, com rebaixamento (R5) |
| `plataforma.py` | Regras de reserva (limite por conta, R2, R3), pagamento, expiração (TTL, R4), fila e redistribuição (R1) |
| `borda.py` | Porta de entrada dos compradores: limite de requisições, idempotência (DA3) e respostas (R6, DA5) |

## Exemplo de uso

```python
from ingresso_adversarial import carregar_parametros, criar_ambiente

parametros = carregar_parametros()
plataforma, borda = criar_ambiente(parametros, parametros.politica_inicial, semente=42, rodada=1)

borda.cadastrar("a2-1", cluster="X")
resposta = borda.reservar("a2-1", 1, chave="r-1")
plataforma.avancar()                 # passa 1 tick: expira reservas e ofertas vencidas
plataforma.verificar_invariantes()   # lista vazia = tudo certo
plataforma.log.salvar("logs/execucao.jsonl")
```

- **Compradores (A1 e o bot de A2)** só usam a `Borda` e só veem `RespostaBorda`.
- **A3** só usa `plataforma.aplicar_politica(...)`, `rebaixar_na_fila(...)` e
  `cancelar_venda(...)`. Nunca muda o estoque direto (DA4).
- **Telemetria (#9)** pode ler `plataforma.estoque`, `plataforma.reservas` e `plataforma.log`.

## Ciclo de vida do ingresso

| De → para | Quando |
|---|---|
| `DISPONIVEL → RESERVADO` | Alguém reservou |
| `RESERVADO → VENDIDO` | Pagou |
| `RESERVADO → OFERTADO_FILA` | O TTL venceu com R1 ligado e há alguém na fila que pode receber |
| `RESERVADO → DISPONIVEL` | O TTL venceu com R1 desligado (é a falha PE3) ou ninguém da fila pode receber |
| `OFERTADO_FILA → RESERVADO` | Quem estava na fila aceitou |
| `OFERTADO_FILA → OFERTADO_FILA` | Recusou ou não respondeu a tempo: passa ao próximo |
| `OFERTADO_FILA → DISPONIVEL` | A fila acabou |
| `VENDIDO → OFERTADO_FILA` ou `DISPONIVEL` | Cancelamento *a posteriori* (decisão de A3, #11) |

Quem recusa uma oferta ou deixa ela vencer sai da fila. Assim nenhum ingresso fica
preso em `OFERTADO_FILA` (INV5).

## O que o comprador vê

| Situação | R6 desligado (estado inicial) | R6 ligado |
|---|---|---|
| Passou do limite de requisições | `429`, com o limiar em `detalhe` (como na rodada 1) | `403 REJEITADA` |
| Passou do limite de 4 por conta | `403 LIMITE_INGRESSOS`, com o número (regra anunciada) | `403 REJEITADA` |
| R2 pela conta **ou** pelo cluster | `403 LIMITE_RESERVAS`, sem número e sem dizer qual foi | `403 REJEITADA` |
| R3 sem cartão | `402 SEM_CARTAO` | `403 REJEITADA` |
| Ingresso já reservado por outra pessoa | `409 INDISPONIVEL` | `409 INDISPONIVEL` |

O motivo exato fica sempre no log, no evento `requisicao` (DA5).

## Decisões de implementação

- **Idempotência:** a chave vale por conta e por operação durante a rodada inteira. Um
  `429` não é guardado, porque a operação nem foi feita.
- **Limite de requisições:** conta as requisições aceitas nos últimos `janela` ticks.
- **R3:** o custo da pré-autorização fica guardado na reserva. Quanto isso pesa para A2
  é decidido na avaliação de A2 (#10).
- **Política nova no meio da rodada:** vale para as próximas reservas. As reservas que
  já existem continuam com o prazo antigo.
