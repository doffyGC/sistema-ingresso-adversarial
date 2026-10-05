# 3.4 Cenários de ameaça

Este documento descreve os cenários de ameaça no formato do enunciado. Cada cenário parte
de uma das cadeias de pontos de exploração de
[`superficie-ataque.md`](superficie-ataque.md) (seção 5): a cadeia diz **por onde** A2 age,
e o cenário acrescenta **quem** age, **com que intenção** e **com que impacto**. A
pontuação de probabilidade, impacto e risco está em [`riscos.md`](riscos.md), e a resposta
à ameaça prioritária, em [`resiliencia.md`](resiliencia.md).

O vocabulário é o da seção 3.1 ([`contexto.md`](contexto.md)): atores A1 a A3 (seção 2),
ativos (seção 4), pressupostos P1 a P5 (seção 9) e interfaces F1 a F7 (seção 12).

> **Sobre os IDs.** A tabela-modelo do enunciado usa `A1`, `A2`, `A3` para os cenários, mas
> esses IDs já são os **atores** da seção 3.1. Os cenários usam `T1`, `T2`, `T3`.

---

## T1. Imobilização e recaptura de estoque

> Um **comprador adversarial (A2)** pode **abrir reservas em massa sem intenção de pagar,
> deixá-las expirar e reservar de novo o ingresso no instante em que ele volta** por meio
> da **reserva que retém estoque sem custo (PE2), da devolução previsível ao estoque
> público (PE3) e da leitura gratuita da disponibilidade (PE1)**, aproveitando **o
> pressuposto de que uma reserva não paga volta a circular para outro comprador (P2)**,
> causando **a retirada do estoque de circulação e sua concentração em quem monitora em
> alta frequência** sobre a **disponibilidade do estoque e a justiça da alocação**.

| Cadeia | Interfaces | Pressupostos | Rodada |
|---|---|---|---|
| PE2 → PE3 → PE1 | F2, F3, F1 (F4 contribui para PE2) | P2, P4, P5 | 3 |

**Como acontece.** A2 reserva tudo o que consegue (F2), sem custo, e decide depois quais
reservas pagar (F4). As demais expiram após 10 minutos (F3) e voltam à disponibilidade
pública. Como foi A2 quem reservou, ele sabe o instante exato da devolução e está
consultando F1 nesse momento: reserva de novo antes de qualquer A1. O ciclo se repete
enquanto houver interesse em reter o ingresso.

**Por que é adversarial, e não erro.** Nenhuma regra é violada: reservar, deixar expirar e
reservar de novo é o uso projetado. O que muda é a intenção, visível só no padrão — a
conversão reserva → pagamento do cluster muito abaixo da média e a disponibilidade
oscilando em ciclos de exatamente um TTL (rodada 3 do 3.3).

**Catálogo.** OWASP OAT-021, *Denial of Inventory* (ref. 3).

---

## T2. Escala por identidades

> Um **comprador adversarial (A2)** pode **criar ou comprar muitas contas para multiplicar o
> limite de 4 ingressos e as posições na fila sorteada, disparando requisições simultâneas
> para tirar de cada conta mais do que o limite** por meio do **limite por conta apoiado em
> contas baratas (PE4), da fila em que cada conta é um bilhete (PE8) e da verificação do
> limite sem atomicidade (PE5)**, aproveitando **o pressuposto de que uma identidade
> corresponde a uma pessoa (P1) e a verificação e gravação não atômicas do limite**,
> causando **o desvio de parte do lote para quem controla mais contas e reservas acima do
> limite anunciado** sobre a **justiça da alocação e a integridade das reservas**.

| Cadeia | Interfaces | Pressupostos ou fraqueza | Rodada |
|---|---|---|---|
| PE4 → PE8, com PE5 | F5, F6, F2 | P1, P5; verificação do limite não atômica | 2, 3, 4 |

**Como acontece.** A2 cria contas em lote ou compra contas aquecidas (F5). Cada conta vale
um bilhete no sorteio da fila (F6) e mais 4 ingressos no limite (F2). Com requisições
paralelas da mesma conta, várias passam pela leitura do limite antes da primeira gravação,
e a conta termina acima de 4.

**Por que é adversarial, e não erro.** Uma venda duplicada por concorrência é, em si, um
defeito (contraexemplo da seção 3.1, seção 11). Aqui A2 **escolhe** disparar requisições
simultâneas, mede quantas passaram e repete; e as contas existem para contornar o limite,
não para representar pessoas.

**Catálogo.** OWASP OAT-019, *Account Creation* (ref. 3); MITRE CWE-367, TOCTOU (ref. 8), para a parte de PE5.

---

## T3. Calibragem pelos limiares

> Um **comprador adversarial (A2)** pode **usar as mensagens de rejeição para descobrir qual
> regra o barrou, em que limiar e por qual variável, e passar a operar logo abaixo desse
> limiar, rotacionando IPs e contas** por meio das **mensagens de resposta como oráculo
> (PE7), do controle de ritmo com limiar fixo por IP e sessão (PE6) e do limite por conta
> (PE4)**, aproveitando **o pressuposto de que a cadência e o volume revelam se o agente é
> humano (P3)**, causando **a perda de efeito dos controles de detecção e o bloqueio de
> compradores legítimos que recarregam a página** sobre a **justiça da alocação e a
> confiança no processo**.

| Cadeia | Interfaces | Pressupostos | Rodada |
|---|---|---|---|
| PE7 → PE6 → PE4 | F7, F1, F2 | P3, P5 | 1, 2 |

**Como acontece.** O `429` explícito da rodada 1 é determinístico: repetindo a requisição,
A2 descobre em minutos que o limite é de 30 por minuto e que a variável é o IP (F7). Passa
então a distribuir o volume entre proxies, cada origem logo abaixo do limiar (F1, F2), e
aplica o mesmo método ao limite por conta. Do outro lado, o limiar fixo bloqueia A1 quando
ele recarrega a página com ansiedade — o falso positivo previsto em P3.

**Por que é adversarial, e não erro.** A1 também recebe o `429`, mas não o usa para nada.
A2 transforma cada rejeição em experimento, de propósito, para tornar invisíveis os outros
cenários: T3 sozinho não move o estoque, mas é o que permite calibrar T1 e T2.

**Origem.** Rodada 1 do 3.3, em que o `429` explícito entregou o limiar em minutos.

---

## Rastreabilidade

| Cenário | Pontos | Interfaces | Pressupostos ou fraqueza | Ativos | Risco ([`riscos.md`](riscos.md)) |
|---|---|---|---|---|-:|
| **T1** Imobilização e recaptura | PE2, PE3, PE1 | F2, F3, F1 (F4 em PE2) | P2, P4, P5 | Disponibilidade, justiça | 9 |
| **T2** Escala por identidades | PE4, PE8, PE5 | F5, F6, F2 | P1, P5; atomicidade | Justiça, integridade das reservas | 6 |
| **T3** Calibragem pelos limiares | PE7, PE6, PE4 | F7, F1, F2 | P3, P5 | Justiça, confiança | 6 |

Os três cenários cobrem os oito pontos de exploração e os cinco pressupostos da seção 3.1.

**A quarta cadeia de [`superficie-ataque.md`](superficie-ataque.md), antecipação
(PE1 → PE2),** não vira cenário próprio. Ela é o comportamento da rodada 1 — ver o lote
abrir antes e reservar antes de qualquer humano —, e a fila sorteada da rodada 2 removeu a
vantagem de velocidade. O que restou dela aparece dentro de T1: PE1 continua sendo o
sensor da recaptura.

**Os cenários se encadeiam.** A resposta à ameaça prioritária (T1) empurra A2 para T2 — a
disputa migra de P2 para P1 ([`resiliencia.md`](resiliencia.md), seção 3) —, e T3 é o
método que A2 usa para calibrar qualquer um dos dois.
