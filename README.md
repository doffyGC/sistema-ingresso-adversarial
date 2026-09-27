# Trabalho 1 — Análise de um Sistema Adversarial

**Sistema analisado:** plataforma de venda e reserva de ingressos — disputa por ingressos
de um evento de alta demanda.

**Disciplina:** Engenharia de Software Adversarial — Unipampa
**Modalidade:** grupo de 6 integrantes

> **Estado do documento:** em construção. A seção 3.1 está completa; as demais estão
> pendentes. A integração final do README é tarefa coletiva.

---

## 3.1 Descrição do sistema adversarial

> **Documento completo:** [`docs/contexto.md`](docs/contexto.md)

### A interação analisada

O sistema é uma plataforma de venda e reserva de ingressos. **Não analisamos a plataforma
inteira**: o recorte é uma única interação.

> **A tentativa de um comprador obter um ingresso para um evento de alta demanda,
> durante a janela de abertura das vendas, enquanto a plataforma aplica regras de
> controle de disponibilidade para distribuir um estoque finito.**

O fluxo coberto tem três passos: **consultar** a disponibilidade de um setor →
**reservar** temporariamente o ingresso por um prazo (TTL) → **confirmar** o pagamento.
Se o pagamento não ocorre dentro do prazo, a reserva expira e o ingresso retorna ao
estoque.

Ficam fora do escopo: catálogo de eventos, emissão fiscal, check-in na portaria,
reembolso e o mercado secundário em si.

### Atores

- **A1 — Comprador legítimo:** pessoa física, agindo manualmente, que quer um ou poucos
  ingressos para consumo próprio.
- **A2 — Comprador adversarial (cambista/bot):** agente racional e adaptativo que busca
  acumular ingressos para revenda com sobrepreço, investindo em automação e em múltiplas
  identidades.
- **A3 — Plataforma:** media a interação e decide, **sem saber se quem solicita é A1 ou
  A2**, quanto estoque expor, se aceita cada reserva, por quanto tempo ela vale e quanto
  atrito impor.

Atores de contexto, não modelados como jogadores: o **organizador do evento** (pressiona
pela venda rápida, limitando o atrito aceitável) e o **mercado secundário** (define o
retorno esperado de A2).

### Ativo a preservar

> **A distribuição justa e controlada do estoque finito de ingressos** — a alocação deve
> resultar das regras anunciadas pela plataforma, e não da capacidade técnica de
> automatizar tentativas.

Ativos derivados: disponibilidade do estoque, integridade das reservas e confiança no
processo de venda.

### Elementos principais

| Ator | Objetivo | Ações ou capacidades | Informações observáveis | Restrições ou custos |
|---|---|---|---|---|
| **A1 — Comprador legítimo** | Obter o ingresso desejado com esforço razoável | Consultar, selecionar, reservar, pagar, reenviar tentativa manual, aguardar na fila, desistir | Disponibilidade exibida, resultado da tentativa, mensagem de erro, posição na fila, TTL restante | Estoque finito, prazo curto de pagamento, limite por identidade, precisa estar online no horário, baixa tolerância a atrito |
| **A2 — Comprador adversarial** | Capturar o máximo de ingressos de alto valor ao menor custo e risco | Tudo de A1 + automação, paralelismo, múltiplas identidades, rotação de IP/dispositivo, monitoramento de alta frequência, imobilização de estoque, imitação de tráfego humano, terceirização de CAPTCHA | Tudo de A1 + latência e códigos de resposta, qual identidade caiu e após quantas tentativas, instante da liberação do lote, taxa de sucesso por estratégia, histórico entre eventos | Custo de infraestrutura e de contas, risco de banimento e de cancelamento do pedido, capital imobilizado, janela temporal estreita, custo de KYC |
| **A3 — Plataforma** | Distribuir o estoque conforme as regras anunciadas, preservando justiça e disponibilidade | Publicar disponibilidade, aceitar/rejeitar reserva, definir e aplicar TTL, liberar expiradas, limitar por identidade, *rate limiting*, fila de espera, CAPTCHA/verificação, telemetria, cancelar e suspender, escolher a mensagem de resposta | Volume e cadência de requisições, *fingerprint* e origem, histórico de reservas, taxa de conversão reserva→pagamento, correlação entre contas | Capacidade sob pico, custo alto de falso positivo, latência aceitável, pressão do organizador por venda rápida, custo de moderação, exposição reputacional |

A assimetria central: **A2 observa o resultado das regras e pode inferi-las; A3 observa o
comportamento de A2, mas não sua identidade nem sua intenção.** Ambos os lados aprendem
com o que veem, e nenhum enxerga o outro por completo.

### Pressupostos e como podem falhar

| ID | Pressuposto | Modo de falha | Ativo em risco |
|---|---|---|---|
| **P1** | Uma identidade corresponde a uma pessoa | Contas em massa, documentos de terceiros, contas compradas — o limite por identidade deixa de limitar | Justiça da alocação |
| **P2** | Uma reserva não paga volta a circular e beneficia outro comprador | Reservas em massa sem intenção de pagar; o estoque volta, mas para quem monitora em alta frequência. O TTL vira negação de serviço sobre o estoque | Disponibilidade do estoque |
| **P3** | A cadência de requisições distingue humano de bot | Falha nos dois sentidos: o bot imita o humano; o humano ansioso no pico parece bot | Justiça e confiança |
| **P4** | A disponibilidade exibida é única e fiel ao estoque real | Cache e réplicas com atraso; quem consulta a API direto vê o lote antes de quem usa o site | Justiça da alocação |
| **P5** | O custo de tentar é semelhante para todos | A automação zera o custo marginal da tentativa para A2, mas não para A1 — tratamento igual sobre capacidades desiguais não produz resultado justo | Justiça da alocação |

### Por que este caso é adversarial, e não um erro

Um *bug* de concorrência que vende o mesmo assento duas vezes é um defeito: ninguém
escolheu que acontecesse e ele não reage à correção. O caso aqui é diferente:

1. **Há intenção e escolha** — A2 avalia custo, retorno e risco, e decide.
2. **Os objetivos conflitam de fato** — o estoque é finito; cada ingresso capturado por
   A2 é um ingresso a menos para A1.
3. **A regra é o alvo, não o obstáculo acidental** — A2 usa o sistema exatamente como
   projetado, em volume e velocidade que o projeto não previu. Não há erro a corrigir:
   há um incentivo a redesenhar.
4. **Há aprendizado dos dois lados** — cada bloqueio, CAPTCHA ou mensagem de erro informa
   A2 sobre onde está o limiar, e cada defesa nova produz uma contramedida nova.
5. **A defesa tem custo sobre terceiros** — endurecer a regra contra A2 atinge A1, porque
   A3 não consegue distingui-los no momento da decisão.

> O que torna este sistema adversarial não é a existência de uma falha, mas a existência
> de **um agente que lucra com a regra funcionando como projetada, e que reage a toda
> tentativa de impedi-lo.**

---

## 3.2 Modelo estratégico estático

> *Pendente.*
> Insumo disponível: jogadores **A2 × A3**, repertório de ações e restrições de custo em
> [`docs/contexto.md`](docs/contexto.md), seções 5 e 7.

## 3.3 Modelo estratégico dinâmico

> *Pendente.*
> Insumo disponível: assimetria de observação em [`docs/contexto.md`](docs/contexto.md),
> seção 6.

## 3.4 Ameaças e riscos

> *Pendente.*
> Insumo disponível: sete interfaces de fronteira e cinco pressupostos já mapeados entre
> si em [`docs/contexto.md`](docs/contexto.md), seções 9 e 12; ativos na seção 4.

## Resiliência, resposta e arquitetura do Trabalho 2

> *Pendente.*

---

## Estrutura do repositório

```text
sistema-ingresso-adversarial/
├── README.md                     relatório principal
├── docs/
│   ├── contexto.md               3.1
│   ├── modelo-estatico.md        3.2        (pendente)
│   ├── modelo-dinamico.md        3.3        (pendente)
│   ├── ameacas.md                3.4        (pendente)
│   ├── riscos.md                 3.4        (pendente)
│   └── resiliencia.md                       (pendente)
├── diagramas/
│   ├── contexto.svg              Fig. 1 - DFD nivel 0
│   ├── contexto-fluxo.svg        Fig. 2 - fluxo interno
│   ├── contexto-legenda.svg      legenda das duas
│   ├── ciclo-adaptativo.*                   (pendente)
│   ├── superficie-ataque.*                  (pendente)
│   └── arquitetura-t2.*                     (pendente)
└── fontes/
    └── referencias.md            colaborativo
```

## Referências

Ver [`fontes/referencias.md`](fontes/referencias.md).

## Declaração de uso de IA generativa

> *A completar coletivamente antes da entrega.*
>
> **Seção 3.1:** foram utilizados assistentes de IA generativa (ChatGPT e Claude) no
> *brainstorming* da escolha do sistema, no recorte da interação analisada e na redação
> da seção. O conteúdo foi revisado manualmente quanto à aderência ao enunciado, à
> consistência do recorte e à correção das referências citadas.
