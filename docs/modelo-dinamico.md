# 3.3 Modelo estratégico dinâmico

## Objetivo e recorte

O modelo estático (3.2) é uma **fotografia**: mostra o que cada jogador prefere em uma
única interação. Este modelo é o **filme**: mostra como as escolhas mudam quando a
interação se repete e cada lado observa o resultado da anterior. Os jogadores continuam
sendo **A2 (comprador adversarial)** e **A3 (plataforma)**; **A1 (comprador legítimo)** não
decide estrategicamente, mas é afetado em toda rodada e seus custos são registrados
explicitamente.

O ponto de partida vem do próprio 3.2: a matriz não tem equilíbrio de Nash em estratégias
puras, e as melhores respostas formam um ciclo.

```text
(I, P) ──A3 passa a controlar──► (I, C) ──A2 recua──► (R, C) ──A3 relaxa──► (R, P) ──A2 escala──► (I, P)
```

No modelo estático, a resposta de A2 ao controle é **recuar** para Regular. Na interação
real, A2 tem uma terceira saída que a matriz 2×2 não representa: **mantém o mesmo objetivo
e muda a ação**, contornando o controle novo em vez de aceitá-lo. O que significa
"Intensivo" muda a cada rodada — o repertório de ações não é fixo, ele cresce.

## Unidade de análise: a rodada

Uma **rodada** é uma abertura de vendas (um lote ou um evento). É entre uma abertura e
outra que A3 muda suas regras e que A2 reconfigura sua infraestrutura. Dentro de uma mesma
abertura também há reações rápidas (um *rate limit* reage em segundos), mas a mudança de
estratégia de ambos acontece entre aberturas.

Toda rodada percorre o ciclo pedido, com os fluxos e interfaces da seção 3.1:

| Etapa | O que acontece | Fluxo / interface |
|---|---|---|
| **Ação** | A2 executa a estratégia calibrada na rodada anterior | f3; F1, F2, F4, F5 |
| **Resposta** | A3 aplica ou ajusta um controle, com base no que sua telemetria mostrou — e o controle atinge também A1 | F2, F3, F6; f2 |
| **Observação** | A2 lê as respostas como sinal de calibragem; A3 lê o comportamento resultante | f4, F7; telemetria |
| **Adaptação** | Cada lado escolhe a estratégia da rodada seguinte com o que aprendeu | linhas tracejadas da Fig. 2 |

### Informação disponível a cada jogador

Os dois lados não observam a mesma coisa:

- **A3 decide observando comportamento, sem observar identidade.** Ela vê que uma sessão
  faz 40 requisições por minuto, não vê se é um bot ou uma pessoa ansiosa.
- **A2 decide observando o resultado das regras, sem observar as regras.** Ele vê que a
  conta caiu na 31ª tentativa, não vê o código que a derrubou — mas, repetindo o
  experimento, estima o limiar.

Isso cria uma **assimetria de velocidade de aprendizado**: A2 aprende com cada tentativa
(milhares por abertura, custo marginal próximo de zero, pressuposto P5), enquanto A3
aprende com padrões agregados e precisa de confiança estatística antes de agir, porque
errar custa um falso positivo sobre A1. Por isso, nas rodadas abaixo, **A3 tende a reagir
e A2 tende a antecipar**.

## Estado inicial

Regras ordinárias anunciadas: limite de 4 ingressos por identidade e reserva com TTL de
10 minutos, sem controle de ritmo. Na abertura anterior, poucas origens automatizadas
concentraram o volume e o lote esgotou em segundos — a regra anunciada foi cumprida e,
ainda assim, a distribuição não foi justa. Na matriz do 3.2, é a célula
**(I, P) = (4, 0)**: o pior resultado para A3, que é quem tem incentivo para mudar.

Os controles e contramedidas abaixo vêm do repertório da seção 3.1, seção 5. Os limiares
numéricos são ilustrativos, escolhidos para tornar o raciocínio concreto; não são dados de
uma plataforma real.

## Rodadas

### Rodada 1 — Limitação de ritmo

- **Ação de A2:** poucas contas, automação consultando a disponibilidade (F1) em alta
  frequência e reservando no instante em que o lote abre.
- **Resposta de A3:** *rate limiting* por IP e por sessão — por exemplo, 30 requisições por
  minuto — com resposta `429 Too Many Requests` explícita. A3 escolhe comunicar o motivo
  para não deixar A1 confuso.
- **O que se torna observável:**
  - **A2** vê que o 429 aparece sempre no mesmo ponto. Repetindo a requisição, confirma que
    a regra é **determinística** e **associada ao IP**. Em minutos sabe onde está o limiar
    e qual variável o controla.
  - **A3** vê o volume por origem cair e o limite sendo atingido por poucas origens.
- **Custo para A1:** o comprador que recarrega a página compulsivamente no pico também
  recebe 429. É o **falso positivo** previsto em P3 — o humano ansioso parece bot.
- **Adaptação para a rodada 2:** A2 distribui as requisições abaixo do limiar descoberto.
  A3, sabendo que o controle por IP é contornável, passa a registrar *fingerprint* de
  dispositivo e data de criação das contas.

> **A mensagem de erro ensinou o adversário.** O mesmo dado que orienta A1 entregou a A2 o
> limiar e a variável que o controla (f2 = f4, seção 3.1). Na matriz, a rodada passou por
> **(I, C) = (1, 2)** só durante a abertura — na seguinte, o controle já não alcança A2.

### Rodada 2 — Rotação de origem e fila de espera

- **Ação de A2:** rotação de IP por proxies, muitas contas criadas em lote na véspera,
  cada origem mantida logo abaixo de 30 requisições por minuto, com intervalos irregulares
  para imitar cadência humana. O objetivo não mudou; a ação mudou.
- **Resposta de A3:** **fila de espera com ordem sorteada** antes da abertura e **CAPTCHA**
  no passo de reserva (F2, F6). A fila remove a vantagem de velocidade — chegar 100 ms
  antes deixa de importar —, e o CAPTCHA encarece cada tentativa automatizada.
- **O que se torna observável:**
  - **A2** vê que a fila é sorteada, então o que conta é **quantas posições** ele ocupa —
    cada conta vira um bilhete de sorteio. Vê também que o CAPTCHA aparece em toda reserva,
    sem exceção: é um custo fixo por tentativa, não uma detecção.
  - **A3** vê que o limite por IP parou de disparar, mas encontra a mesma *fingerprint* em
    IPs diferentes e um pico de contas criadas na véspera (P1).
- **Custo para A1:** a fila **melhora** a situação de A1, que deixa de competir por
  reflexo. O CAPTCHA a **piora**: soma atrito, e parte dos compradores legítimos desiste
  (tolerância a atrito, seção 7). Usuários com deficiência visual ou conexão lenta são os
  mais atingidos.
- **Adaptação para a rodada 3:** A2 terceiriza a resolução de CAPTCHA, multiplica contas
  para ocupar mais posições na fila e passa a reter estoque em vez de só comprar. A3 passa
  a acompanhar a conversão reserva → pagamento por cluster de contas correlacionadas.
- **Herança da rodada 1:** A2 só consegue ficar "logo abaixo do limiar" porque a rodada 1
  revelou o limiar.

### Rodada 3 — Imobilização de estoque e controle da informação

- **Ação de A2:** com o CAPTCHA terceirizado (um custo por resolução, previsível), **reserva
  em massa sem intenção de pagar** e deixa as reservas expirarem, recapturando o estoque
  quando ele volta (P2; OWASP OAT-021, *Denial of Inventory*). Assim escolhe os melhores
  assentos e decide depois quais pagar.
- **Resposta de A3:** a conversão reserva → pagamento de um cluster de contas cai muito
  abaixo da média, e a disponibilidade oscila em ciclos de exatamente 10 minutos. A3
  responde com:
  - **TTL reduzido** (de 10 para 5 minutos) e **limite de reservas ativas** por cluster;
  - **pré-autorização do cartão** no momento da reserva, para que reservar custe algo a
    quem não paga;
  - **mensagem genérica** em toda rejeição ("não foi possível concluir sua reserva"), sem
    código específico — a lição da rodada 1;
  - **marcação silenciosa**: contas suspeitas não são bloqueadas na hora; são monitoradas
    e **canceladas *a posteriori*** (seção 5).
- **O que se torna observável:**
  - **A2**, pela primeira vez, recebe um sinal **pior**. A rejeição não diz o motivo, e o
    cancelamento chega dias depois, misturando o efeito de várias decisões. A2 não sabe
    mais qual comportamento derrubou qual conta.
  - **A3** vê o ciclo de 10 minutos desaparecer e a conversão do cluster subir — ou as
    contas sumirem.
- **Custo para A1:** TTL de 5 minutos pune quem paga devagar (cartão recusado,
  autenticação bancária demorada). A pré-autorização exclui quem não tem cartão de crédito.
  A mensagem genérica deixa A1 sem saber o que fez de errado. O cancelamento *a posteriori*,
  se atingir uma conta legítima, é o falso positivo mais caro do sistema: o comprador
  achava que tinha o ingresso.
- **Adaptação para a rodada 4:** sem saber quais contas foram descobertas, A2 para de
  confiar em contas criadas em lote e passa a investir em identidades que não se
  correlacionam. A3 passa a olhar o padrão de compra, já que a correlação técnica deixou de
  funcionar.
- **Herança da rodada 2:** a fila sorteada transformou cada conta em um bilhete, o que
  empurrou A2 a multiplicar contas — e são essas contas correlacionadas que, agora,
  denunciam o cluster. Do lado de A3, a fila e o CAPTCHA já foram anunciados: retirá-los
  agora pareceria piorar a venda, então os controles novos se **somam** aos anteriores.

### Rodada 4 — Ataque à identidade

- **Ação de A2:** troca contas criadas em lote por **contas antigas compradas
  ("aquecidas")**, cada uma com cartão próprio, que não se correlacionam entre si (P1).
  Cada identidade passa a ser cara de obter e cara de perder.
- **Resposta de A3:** **verificação de identidade seletiva** (documento ou KYC) para
  compras acima de um certo valor e para contas antigas que só compram em eventos de alta
  demanda.
- **O que se torna observável:**
  - **A2** vê **quais** contas foram chamadas à verificação e passa a estimar o critério
    de seleção (valor da compra, histórico da conta).
  - **A3** vê quantas contas abandonam o pedido na etapa de verificação — um indicador de
    que não havia uma pessoa real disposta a se identificar.
- **Custo para A1:** mais um passo de cadastro e exposição de dados pessoais; aumenta a
  desistência, sobretudo de quem compra pela primeira vez.
- **Adaptação seguinte:** A2 passa a usar **identidades de pessoas reais** (familiares,
  laranjas pagos) que aceitam se verificar, e limita cada uma a compras abaixo do critério
  observado. É a forma mais cara de contornar P1, mas não é impossível. A defesa da rodada 4
  **não encerra** o ciclo: muda o recurso em disputa de "contas" para "pessoas".
- **Herança da rodada 3:** o cancelamento *a posteriori* tornou cada conta perdida mais
  cara para A2, o que justifica pagar por contas aquecidas.

## Síntese das rodadas

| Rodada | Ação do participante (A2) | Resposta do sistema ou defensor (A3) | O que se torna observável? | Adaptação para a rodada seguinte | Custo para A1 |
|-:|---|---|---|---|---|
| **1** | Automação e monitoramento de alta frequência, poucas contas | *Rate limit* por IP com 429 explícito | **A2:** limiar exato e a variável que o controla (IP). **A3:** volume concentrado em poucas origens | **A2:** distribuir abaixo do limiar. **A3:** registrar *fingerprint* e idade das contas | Humano ansioso bloqueado (falso positivo) |
| **2** | Rotação de IP, contas em lote, cadência humana | Fila sorteada + CAPTCHA | **A2:** fila premia número de contas; CAPTCHA é custo fixo. **A3:** *fingerprints* repetidas, contas da véspera | **A2:** terceirizar CAPTCHA, multiplicar contas, reter estoque. **A3:** medir conversão por cluster | Fila ajuda; CAPTCHA gera desistência |
| **3** | Reservas em massa sem pagamento, CAPTCHA terceirizado | TTL menor, limite por cluster, pré-autorização, mensagem genérica, cancelamento *a posteriori* | **A2:** sinal genérico e atrasado. **A3:** ciclo de 10 min some, conversão sobe | **A2:** identidades que não se correlacionam. **A3:** analisar padrão de compra | Prazo curto, exclusão de quem não tem cartão, risco de cancelamento indevido |
| **4** | Contas aquecidas, cartões distintos | Verificação de identidade seletiva | **A2:** quais contas são verificadas. **A3:** abandono na etapa de verificação | **A2:** identidades de pessoas reais abaixo do critério | Cadastro mais longo, exposição de dados |

## Diagrama do ciclo adaptativo

![Ciclo adaptativo em quatro rodadas](../diagramas/ciclo-adaptativo.png)

**Fonte editável:** `diagramas/ciclo-adaptativo.mmd` (Mermaid). **Exportado:**
`diagramas/ciclo-adaptativo.svg` e `.png`. A figura acima referencia o `.png` porque o
SVG do Mermaid guarda os rótulos em `foreignObject`, que não é renderizado quando o SVG é
embutido como imagem.

Cada bloco é uma rodada, com a ação de A2 (vermelho), a resposta de A3 (azul), o que se
torna observável (branco) e o custo para A1 (verde) — as cores da legenda da seção 3.1. As
setas contínuas acontecem dentro da rodada; as tracejadas são a adaptação, que só tem
efeito na rodada seguinte.

## O que a sequência mostra

**A resposta do sistema também produz informação.** Na rodada 1, A2 aprende rápido e com
precisão porque a resposta é imediata, explícita e determinística. Cada tentativa é um
experimento barato.

**A3 aprende devagar, mas aprende sobre a população.** Ela não identifica *quem* é A2;
identifica *padrões* — correlação entre contas, conversão anômala, oscilação periódica do
estoque. Cada padrão leva pelo menos uma abertura inteira para ser confirmado.

**A virada da rodada 3** é a mais importante do modelo: A3 deixa de competir só em
**controles** e passa a competir em **informação**. Três decisões degradam o canal de
aprendizado de A2 sem endurecer a regra:

| Decisão de A3 | Efeito sobre o sinal que A2 recebe |
|---|---|
| Mensagem genérica em vez de código específico | A2 não distingue qual regra o barrou |
| Cancelamento *a posteriori* em vez de bloqueio imediato | O sinal chega atrasado e misturado; A2 não liga causa a efeito |
| Marcação silenciosa | A2 não sabe quais contas já estão comprometidas e continua investindo nelas |

O custo também recai sobre A1, que recebe a mesma mensagem genérica e o mesmo
cancelamento tardio. **Opacidade é uma defesa contra A2 e uma perda de transparência para
A1** — a mesma tensão do 3.2, agora no plano da informação.

**Os custos para A1 se acumulam.** Na rodada 4, o comprador legítimo enfrenta fila,
CAPTCHA, prazo curto, pré-autorização, mensagens pouco explicativas e verificação de
identidade. Nenhum deles sozinho é proibitivo; juntos, consomem o **orçamento de atrito**
que A1 tolera antes de desistir (seção 7). Se A1 desiste, o estoque volta para quem
persiste com menor custo — e esse é A2, que automatizou cada etapa. Uma defesa calibrada
sem considerar A1 pode **aumentar** a fatia de A2. O critério de A3, portanto, não é "qual
controle bloqueia mais", e sim "qual controle custa mais para A2 do que para A1". A fila
sorteada da rodada 2 é o melhor exemplo: custa pouco a A1 e anula uma vantagem inteira
de A2.

## Perguntas de fechamento

**Quem observa quem?**
A3 observa o **comportamento** de A2 — volume, cadência, *fingerprint*, conversão —, mas
não sua identidade nem sua intenção. A2 observa as **respostas** de A3 — códigos, mensagens,
bloqueios, cancelamentos —, mas não as regras. A1 observa as mesmas respostas que A2, sem
capacidade de usá-las como experimento. Nenhum lado vê o outro por completo.

**O que cada lado consegue mudar?**
A2 muda **como** tenta: velocidade, número de origens, número e qualidade das identidades,
e o próprio objetivo tático (comprar ou reter). Não muda o estoque nem as regras. A3 muda
as **regras** (limites, TTL, fila, verificação) e — a partir da rodada 3 — **quanta
informação** cada resposta carrega. Não muda o preço de revenda (f8), que sustenta o
incentivo de A2.

**O que dispara uma adaptação?**
Para A2, a **queda na taxa de sucesso** de uma estratégia, medida sobre muitas tentativas.
Para A3, uma **anomalia agregada** que se confirma ao longo de uma abertura: esgotamento em
segundos (rodada 1), *fingerprints* repetidas (rodada 2), conversão baixa e oscilação
periódica do estoque (rodada 3), contas antigas que só compram em eventos de alta demanda
(rodada 4).

**Qual é o custo da adaptação para cada lado?**

| Lado | Custo de adaptar |
|---|---|
| **A2** | Infraestrutura (proxies, servidores), contas cada vez mais caras (em lote → aquecidas → pessoas reais), resolução de CAPTCHA, capital retido em pré-autorizações, perdas por cancelamento *a posteriori* |
| **A3** | Desenvolvimento e operação dos controles, capacidade no pico, moderação manual, perda de transparência — e, sobretudo, o **custo pago por A1** em atrito e falsos positivos, que volta para A3 como perda de receita e reputação |

**Em que ponto pode surgir uma corrida armamentista?**
Na **rodada 2 para a 3**: o CAPTCHA é um controle de custo fixo, e A2 compra a
resolução no mercado — cada endurecimento do CAPTCHA aumenta o atrito de A1 mais do que o
custo de A2. E, de forma mais grave, na **identidade (rodadas 3 e 4 em diante)**: contas em
lote levam a correlação; contas aquecidas levam a verificação; verificação leva a laranjas.
Cada passo é mais caro para os dois lados e mais invasivo para A1.

A corrida só se estabiliza por uma condição econômica. A2 continua escalando enquanto:

```text
n × q × (preço de revenda − preço de face)  >  custo de infraestrutura + custo de identidades + perdas esperadas por cancelamento
```

onde `n` é o número de ingressos que A2 tenta capturar e `q` a fração que ele efetivamente
consegue pagar e revender sem cancelamento. Assim, **A3 não precisa detectar todo A2**:
precisa que o lado direito cresça mais rápido que o esquerdo, sem consumir o orçamento de
atrito de A1. Os controles que atuam sobre `q` (cancelamento *a posteriori*,
pré-autorização) e sobre o custo de identidade são os que mais pesam, porque atingem o que
A2 não consegue automatizar.

## Limitações

- As rodadas são uma **sequência plausível**, não a única. A2 poderia, por exemplo,
  começar pela imobilização de estoque; a ordem escolhida segue a escalada de custo, do
  mais barato ao mais caro para o adversário.
- A3 é tratada como um único decisor. Na prática, as regras mudam também por pressão do
  organizador (que quer venda rápida) e por limites de capacidade no pico, o que pode
  atrasar ou suavizar as respostas.
- Os limiares (30 requisições por minuto, TTL de 10 e 5 minutos) são ilustrativos.
- O modelo não estima probabilidades, custos monetários nem taxas reais de falso positivo;
  a condição econômica é qualitativa.
- A1 é representado como afetado, não como jogador: o modelo não trata o caso em que
  compradores legítimos também adaptam seu comportamento (por exemplo, usando extensões
  para recarregar a página), o que borra ainda mais a fronteira de P3.
