# 3.4 Avaliação de riscos

Este documento pontua os cenários de ameaça de [`ameacas.md`](ameacas.md) e escolhe a
ameaça prioritária, tratada em [`resiliencia.md`](resiliencia.md). Os ativos são os da
seção 3.1 (seção 4); os pressupostos, P1–P5 (seção 9).

---

## 1. Escala

O enunciado define a escala de 1 a 3 e o risco como **probabilidade × impacto**. Para que a
nota de cada cenário seja justificável, e não arbitrária, cada nível é definido abaixo em
termos deste sistema.

### Probabilidade — quão provável é que A2 execute o cenário

A probabilidade depende do **custo de A2 para executar** e de **quanto o sistema atual
facilita**, e não da frequência medida em uma plataforma real (que não temos).

| Nível | Critério |
|-:|---|
| **1 — baixa** | Exige recursos que A2 não automatiza nem compra pronto: identidades de pessoas reais dispostas a se verificar, acesso privilegiado, ou uma condição rara do sistema |
| **2 — média** | Exige infraestrutura disponível no mercado, mas com custo por tentativa: proxies, contas criadas em lote, resolução de CAPTCHA terceirizada |
| **3 — alta** | Explorável com automação simples e custo marginal próximo de zero (P5), usando o sistema exatamente como projetado; catalogado como ameaça automatizada conhecida (OWASP OAT) |

### Impacto — quanto o cenário compromete os ativos

| Nível | Critério |
|-:|---|
| **1 — baixo** | Atinge poucos ingressos, é reversível dentro da mesma abertura e não altera quem recebe o lote |
| **2 — médio** | Desvia uma parte relevante do lote **ou** impõe a A1 um custo visível (rejeição, atraso, atrito) em uma abertura, atingindo um ativo |
| **3 — alto** | Compromete a alocação da maior parte do lote, **ou** atinge mais de um ativo ao mesmo tempo, **ou** causa dano irreversível a A1 (perder o ingresso, ter o pedido cancelado) ou à confiança no processo para além do evento |

### Faixas de risco

Com notas de 1 a 3, o produto só assume os valores 1, 2, 3, 4, 6 e 9.

| Risco | Faixa | Tratamento |
|-:|---|---|
| **6–9** | Alto | Resposta obrigatória antes da próxima abertura |
| **3–4** | Médio | Resposta planejada; monitorar o indicador correspondente |
| **1–2** | Baixo | Aceitar e monitorar |

**Desempate.** Entre cenários com o mesmo risco, tem prioridade o que (1) atinge mais
ativos, (2) custa menos para A2 executar e (3) causa dano menos reversível a A1, nessa
ordem.

---

## 2. Tabela de riscos

> **Pendente:** as linhas dependem dos cenários e pontos de exploração de
> [`ameacas.md`](ameacas.md). A linha da imobilização de estoque está pré-preenchida para
> que a escolha da ameaça prioritária seja verificável; o ID e o texto devem ser trocados
> pelos daquele arquivo.

> **Atenção aos IDs:** o modelo de tabela do enunciado usa `A1`, `A2`, `A3` para os
> cenários, mas esses IDs já são os **atores** da seção 3.1. Sugestão: usar `T1`, `T2`,
> `T3` para os cenários de ameaça.

| ID | Cenário de ameaça | Ponto de exploração | Pressuposto ou fraqueza | Ativo afetado | Probabilidade | Impacto | Risco |
|-|-|-|-|-|-:|-:|-:|
| T? | A2 abre reservas em massa sem intenção de pagar e recaptura o estoque quando ele expira | F2 (criação de reserva), F3 (expiração e devolução) | P2 — reserva não paga volta a circular para outro comprador | Disponibilidade do estoque; justiça da alocação | 3 | 3 | **9** |
| T? | *pendente* | | | | | | |
| T? | *pendente* | | | | | | |

### Justificativa das notas

**Imobilização de estoque — probabilidade 3.** Reservar não custa nada a quem não pretende
pagar, a reserva funciona exatamente como projetada e a automação necessária é a mesma da
rodada 1. É uma ameaça automatizada catalogada (OWASP OAT-021, *Denial of Inventory*).

**Imobilização de estoque — impacto 3.** Atinge dois ativos ao mesmo tempo: tira ingressos
de circulação (disponibilidade) e os devolve a quem monitora em alta frequência (justiça).
A escala não depende de quantas contas A2 tem, e sim de quantas reservas consegue manter
abertas — pode cobrir o lote inteiro. A1 vê o estoque oscilar e conclui que esgotou, o que
atinge também a confiança no processo.

---

## 3. Ameaça prioritária

Com risco 9, a imobilização de estoque é a ameaça prioritária, **a confirmar** quando os
outros cenários forem pontuados: só outro cenário com risco 9 poderia disputar a
prioridade, e o desempate acima favorece a imobilização, por atingir dois ativos.

A resposta, a adaptação esperada de A2 e o risco residual estão em
[`resiliencia.md`](resiliencia.md).

---

## 4. Risco residual da ameaça prioritária

Pontuação da mesma ameaça **depois** da resposta R1–R6 de [`resiliencia.md`](resiliencia.md):

| Momento | Probabilidade | Impacto | Risco | Faixa |
|---|-:|-:|-:|---|
| Antes da resposta | 3 | 3 | 9 | Alto |
| Depois da resposta | 2 | 2 | 4 | Médio |

**Probabilidade cai de 3 para 2.** Com o limite de reservas ativas (R2) e a pré-autorização
(R3), cada ingresso retido passa a exigir uma identidade com cartão próprio — infraestrutura
que se compra, mas com custo por tentativa. A recaptura, que tornava a imobilização
lucrativa, deixa de render (R1).

**Impacto cai de 3 para 2.** O ingresso liberado volta para a fila de espera, e não para o
adversário (R1): a justiça da alocação deixa de ser atingida pela expiração. Continua
atingida a disponibilidade, enquanto as reservas estão abertas, em escala limitada ao
número de identidades de A2.

**Por que não cai mais.** A2 com identidades reais e capital continua imobilizando em escala
menor, e a detecção (R5, R6) só se confirma ao longo de uma abertura. Baixar o risco para
a faixa baixa exige atuar sobre P1 — a verificação de identidade da rodada 4 —, e não
sobre a reserva.
