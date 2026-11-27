# Simulação de uma abertura de vendas (T2)

Uma rodada do T1 é uma abertura de vendas (D4). A simulação faz a abertura acontecer: a
população A1 e o bot de A2 fazem requisições na Borda, o relógio avança e, no fim, cada lado
recebe o que consegue observar. Ela fica sobre o [núcleo do ambiente](nucleo-ambiente.md) e
não toma decisão de agente: a estratégia de A2 e a política de A3 entram prontas.

## Como usar

```python
from ingresso_adversarial import carregar_parametros
from ingresso_adversarial.simulacao import executar_rodada

parametros = carregar_parametros()
resultado = executar_rodada(1, politica, estrategia, bot_a2, parametros, semente=42)

resultado.observacao_a2   # vai para o agente A2 (#10)
resultado.observacao_a3   # vai para o agente A3 (#11)
resultado.indicadores     # verdade da rodada, só para a análise (#13)
```

Para guardar o log JSONL da rodada, passe um `Log` em `log=` e salve depois com
`log.salvar(...)`. Com a mesma semente, a rodada gera o mesmo resultado e o mesmo log.

## Arquivos (`src/ingresso_adversarial/simulacao/`)

| Arquivo | O que faz |
|---|---|
| `identidades.py` | Ids opacos de contas e clusters (`c04821`, `k00917`); só a rodada sabe quem é A1 e quem é A2 |
| `populacao.py` | População A1, sorteada pela semente |
| `rodada.py` | Executa a abertura tick a tick; define `Participante` e `BordaObservada` |
| `telemetria.py` | Amostra o estoque a cada tick e agrega o log no fim |
| `indicadores.py` | `Indicadores` da rodada (A1 × A2) |
| `observacoes.py` | `ObservacaoA2` e `ObservacaoA3` |

## Uma rodada

1. Cria a Plataforma e a Borda com a política de A3 da rodada.
2. Sorteia a população A1 e cadastra as contas. O bot de A2 cadastra as suas pedindo ids a
   `IdentidadesA2`, que só cria contas e clusters e não revela o dono das outras contas.
3. A cada tick, os participantes agem numa **ordem sorteada**, então requisições de A1 e de
   A2 se intercalam. Depois a Plataforma expira reservas e ofertas e a telemetria tira uma
   amostra.
4. No fim (`duracao_abertura`, 1800 ticks = 30 min), a telemetria agrega o log e são montados
   os indicadores e as observações.

## O bot de A2 (#10)

A rodada aceita qualquer objeto com o formato de `Participante`:

```python
class Participante(Protocol):
    def cadastrar(self, borda, identidades): ...   # identidades.nova_conta(), novo_cluster()
    def agir(self, tick, borda): ...               # as requisições deste tick
```

O bot recebe uma `BordaObservada`, não a Borda. Ela só expõe as operações do comprador
(`ver_disponiveis`, `reservar`, `pagar`...), então `borda.plataforma` dá erro, e ela guarda
cada pedido com a resposta para montar a `ObservacaoA2`. Em `tests/bot_falso.py` há um bot
mínimo (INTENSIVO e REGULAR), usado só nos testes.

## População A1

Os parâmetros estão em `[populacao_a1]` de `config/parametros.toml`. Cada comprador:

- chega num tick entre 0 e `chegada_max` e quer 1 ou 2 ingressos;
- consulta a disponibilidade, reserva (prefere premium em metade das vezes) e paga depois de
  um tempo próprio. Metade desse tempo depois de reservar, inicia o pagamento, o que conta
  para a prorrogação do R4;
- depois de `tentativas_antes_da_fila` "indisponível", desiste ou entra na fila. Na fila, aceita
  a oferta com probabilidade `aceita_oferta`.
- se o pagamento leva 429, **mantém a reserva** e repete o pedido no tick seguinte (a Borda
  não guarda o 429, então a mesma chave serve). Com R6, o 429 chega como `REJEITADA`
  genérica: sem saber o motivo, o comprador insiste enquanto o prazo que recebeu ao reservar
  não passou. Assim, o dano do limite de requisições aparece como falso positivo, e não como
  expiração ou desistência por prazo. Nos ticks em que paga, o ansioso não consulta a reserva:
  pagar tem prioridade.

| Variação | Efeito |
|---|---|
| **Sem cartão** (15%) | Com R3 ligado, a pré-autorização recusa e ele tende a desistir (`verificacao`) |
| **Ansioso** (20%) | Age a cada tick e confere a reserva enquanto paga. Com limite de requisições, leva 429: é o falso positivo de P3 |
| **Prazo curto** | O tempo para pagar segue uma distribuição com cauda que passa do TTL. Quem perde a reserva pode desistir (`prazo`) |
| **Atrito da fila** | Parte desiste em vez de entrar na fila (`fila`); quem entra pode recusar a oferta quando chega a vez (`oferta`) |

## O que cada lado observa

É a assimetria do T1: os dois lados olham a mesma abertura por janelas diferentes.

| | `ObservacaoA2` | `ObservacaoA3` |
|---|---|---|
| Fonte | Só as respostas da Borda ao bot | Telemetria da plataforma |
| Vê | Respostas por categoria, limiares expostos (o `detalhe` de um 429, por exemplo), reservas obtidas, expiradas, recapturas, compras, ofertas da fila, custo de pré-autorização | Requisições, rejeições pelo **motivo exato**, conversão geral e por cluster, estoque retido por minuto, periodicidade das devoluções, vendidos, contas rebaixadas, desistências |
| Não vê | O estoque, outras contas, clusters, motivo interno de rejeição | Quem é A1 e quem é A2 (os ids são opacos) |

**Com R6 ligado**, A1 também recebe só a resposta genérica: `SEM_CARTAO` e o 429 chegam
como `REJEITADA`. Sem saber o motivo, o comprador trata a recusa como uma tentativa
frustrada (conta para ir à fila ou desistir por `fila`), e a desistência por `verificacao`
deixa de acontecer. É de propósito: A1 não tem como saber que foi a pré-autorização. Por
isso, ao comparar rodadas, as desistências por motivo só são comparáveis entre políticas
com o R6 no mesmo estado; o total de desistências vale sempre.

**Periodicidade:** é o intervalo mais comum entre devoluções de ingressos ao público. A
recaptura em ciclos (PE3) aparece como devoluções a intervalos regulares.

## Indicadores

`Indicadores` é a verdade da rodada e nunca vai para os agentes:

- ingressos de A1 e de A2, e quantos deles são premium;
- conversão reserva → pagamento de cada lado;
- estoque retido médio;
- desistências de A1;
- falsos positivos: contas A1 barradas por um controle (limite de requisições, R2, R3),
  rebaixadas na fila ou com venda cancelada.

`contestacoes` e `ganho_a2` ficam em 0 por enquanto. A contestação depende do INV7 (#11), e o
ganho de A2 é a avaliação da #10.

## Critérios de aceite da #9

- **Intensivo × Permitir:** sem controles, A2 intensivo fica com a maior parte do **premium**.
  Com 10 contas e 4 ingressos por conta, A2 chega a no máximo 40 dos 100 ingressos, então o
  critério é medido no setor que A2 quer revender. Com A2 regular, A1 fica com a maior parte do lote.
- **Observação de A2 sem dado interno:** `observacao_a2` só recebe os pedidos e as respostas
  do bot. O teste confere que o JSON não tem contas de A1, clusters, motivos internos nem
  estados do estoque.
- **Determinismo:** mesma semente, mesmo `ResultadoRodada` e mesmo log.

Os testes estão em `tests/test_populacao.py`, `tests/test_rodada.py` e
`tests/test_simulacao_criterios.py`.
