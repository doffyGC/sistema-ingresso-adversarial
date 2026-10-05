# 3.4 Avaliação de riscos

Este documento pontua os cenários de ameaça de [`ameacas.md`](ameacas.md) e escolhe a
ameaça prioritária, tratada em [`resiliencia.md`](resiliencia.md). Os ativos são os da
seção 3.1 (seção 4); os pressupostos, P1–P5 (seção 9); os pontos de exploração, PE1–PE8 de
[`superficie-ataque.md`](superficie-ataque.md).

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

Cada cenário parte de uma das cadeias de pontos de exploração de
[`superficie-ataque.md`](superficie-ataque.md), seção 5: a cadeia diz **por onde** A2 age, e
o cenário acrescenta quem age, com que intenção e com que impacto. A redação completa de
cada cenário, no formato do enunciado, está em [`ameacas.md`](ameacas.md); os IDs são
`T1`–`T3` porque `A1`–`A3` já são os atores da seção 3.1.

| ID | Cenário de ameaça | Ponto de exploração | Pressuposto ou fraqueza | Ativo afetado | Probabilidade | Impacto | Risco |
|-|-|-|-|-|-:|-:|-:|
| T1 | **Imobilização e recaptura:** A2 abre reservas em massa sem intenção de pagar e recaptura o estoque quando ele expira | PE2 → PE3 → PE1 (F2, F3, F1) | P2, P4, P5 | Disponibilidade do estoque; justiça da alocação | 3 | 3 | **9** |
| T2 | **Escala por identidades:** A2 multiplica contas para multiplicar o limite de 4 ingressos e as posições na fila, e dispara requisições simultâneas para tirar mais de cada conta | PE4 → PE8, com PE5 (F5, F6, F2) | P1, P5; verificação do limite sem atomicidade | Justiça da alocação; integridade das reservas | 2 | 3 | **6** |
| T3 | **Calibragem pelos limiares:** A2 usa as mensagens de rejeição para descobrir o limiar de ritmo e passa a operar logo abaixo dele, rotacionando IPs e contas; o limiar fixo bloqueia A1 | PE7 → PE6 → PE4 (F7, F1, F2) | P3, P5 | Justiça da alocação; confiança no processo | 3 | 2 | **6** |

### Justificativa das notas

**Imobilização de estoque — probabilidade 3.** Reservar não custa nada a quem não pretende
pagar, a reserva funciona exatamente como projetada e a automação necessária é a mesma da
rodada 1. É uma ameaça automatizada catalogada (OWASP OAT-021, *Denial of Inventory*).

**Imobilização de estoque — impacto 3.** Atinge dois ativos ao mesmo tempo: tira ingressos
de circulação (disponibilidade) e os devolve a quem monitora em alta frequência (justiça).
A escala não depende de quantas contas A2 tem, e sim de quantas reservas consegue manter
abertas — pode cobrir o lote inteiro. A1 vê o estoque oscilar e conclui que esgotou, o que
atinge também a confiança no processo.

**Escala por identidades — probabilidade 2.** Cada ingresso a mais exige uma conta a mais
(PE4), e cada posição a mais na fila também (PE8). Contas criadas em lote ou compradas são
infraestrutura de mercado, mas com custo por conta — e a rodada 2 já mostrou A2 pagando
esse custo. O paralelismo de PE5 é gratuito, mas só multiplica o que cada conta já obtém.

**Escala por identidades — impacto 3.** Atinge dois ativos: a justiça da alocação, porque o
lote vai para quem controla mais contas, e a integridade das reservas, porque requisições
simultâneas fazem uma conta passar do limite (PE5). O desvio cresce com o número de contas,
sem teto imposto pelo sistema atual.

**Calibragem — probabilidade 3.** Descobrir o limiar não custa nada: o `429` explícito é
determinístico e entregou o limiar em minutos na rodada 1 (PE7). Respeitá-lo exige só
cadência controlada e rotação de origem (PE6).

**Calibragem — impacto 2.** Sozinha, a calibragem não move o estoque: ela torna os outros
cenários indetectáveis pelo controle de ritmo. O dano direto é o do limiar fixo sobre A1,
que é bloqueado ao recarregar a página — um custo visível em uma abertura, atingindo a
confiança no processo. Não chega a 3 porque o falso positivo é reversível (o bloqueio
dura um minuto) e não tira o ingresso de quem já o tem.

---

## 3. Ameaça prioritária

Com risco 9, a imobilização de estoque (T1) é a ameaça prioritária: os outros dois
cenários pontuam 6, e só outro cenário com risco 9 poderia disputar a prioridade. Mesmo
nesse caso, o desempate acima favoreceria a imobilização, por atingir dois ativos ao custo
mais baixo para A2.

T2 e T3 ficam na faixa alta e também exigem resposta, mas não são independentes de T1: a
adaptação esperada de A2 à resposta da imobilização é justamente migrar para T2
([`resiliencia.md`](resiliencia.md), seção 3), e T3 é o que A2 usa para calibrar qualquer
um dos dois.

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
que se compra, mas com custo por tentativa (PE2 deixa de ser gratuito). A recaptura, que
tornava a imobilização lucrativa, deixa de render (R1 fecha PE3).

**Impacto cai de 3 para 2.** O ingresso liberado volta para a fila de espera, e não para o
adversário (R1): a justiça da alocação deixa de ser atingida pela expiração. Continua
atingida a disponibilidade, enquanto as reservas estão abertas, em escala limitada ao
número de identidades de A2.

**Por que não cai mais.** A2 com identidades reais e capital continua imobilizando em escala
menor, e a detecção (R5, R6) só se confirma ao longo de uma abertura. Baixar o risco para
a faixa baixa exige atuar sobre P1 — a verificação de identidade da rodada 4 —, e não
sobre a reserva. Em termos de superfície, o que sobra de T1 passa por PE4 e PE8: é o
cenário T2.
