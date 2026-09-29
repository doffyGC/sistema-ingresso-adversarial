# 3.2 Modelo estratégico estático

## Objetivo e recorte

Esta seção modela uma única interação durante a abertura de vendas de um evento de alta demanda. O jogo principal ocorre entre **A2 (comprador adversarial)** e **A3 (plataforma defensora)**. O ativo em disputa é a distribuição justa e controlada do estoque finito de ingressos. O comprador legítimo (A1) não é um jogador separado nesta matriz; os efeitos das decisões sobre ele entram na avaliação dos resultados.

O modelo é estático: cada jogador escolhe uma ação sem observar a escolha do outro naquela rodada e sem adaptar a estratégia a respostas anteriores. A adaptação ao longo de várias rodadas é tratada na seção 3.3.

## Jogadores e ações

Para cumprir o recorte de dois jogadores e duas ações por jogador, as capacidades detalhadas em `docs/contexto.md`, seção 5, são agrupadas nas seguintes alternativas:

**A2 — comprador adversarial**

- **Regular (R):** faz poucas tentativas e solicita reservas sem escalar o comportamento por automação ou múltiplas identidades.
- **Intensivo (I):** automatiza e paraleliza consultas e reservas, podendo usar múltiplas identidades para aumentar a chance de capturar ingressos.

**A3 — plataforma**

- **Permitir (P):** processa as solicitações com os controles ordinários e sem acrescentar uma barreira reforçada à interação.
- **Controlar (C):** aplica medidas adicionais, agrupando limitação de ritmo, fila ou verificação para reduzir tentativas em escala.

Essas ações são abstrações para a matriz, não descrições completas de implementação. Em particular, “permitir” não significa ignorar as regras básicas de venda; significa não acrescentar o controle reforçado representado por C.

## Payoffs e matriz 2×2

Os payoffs são apresentados como **(A2, A3)**. Usamos uma escala ordinal ilustrativa de 0 a 4: valores maiores representam resultados preferidos pelo respectivo jogador. Não são dados empíricos, probabilidades ou valores monetários. A escala serve para explicitar as preferências assumidas pelo modelo.

| A2 \ A3 | Permitir (P) | Controlar (C) |
|---|---:|---:|
| **Regular (R)** | **(3, 3)** | **(2, 1)** |
| **Intensivo (I)** | **(4, 0)** | **(1, 2)** |

**Justificativa dos payoffs:**

- **(R, P) = (3, 3):** A2 tem uma chance razoável de obter ingressos com baixo custo; A3 mantém a experiência fluida e evita impor atrito desnecessário. O resultado para A1 depende da concorrência pelo estoque.
- **(R, C) = (2, 1):** A2 enfrenta barreiras apesar de usar poucas tentativas. A3 reduz parte do risco de abuso, mas assume custo de operação e pode causar falsos positivos ou atrito para A1.
- **(I, P) = (4, 0):** A2 pode converter sua escala em vantagem sobre o estoque. A3 deixa de preservar adequadamente a justiça da alocação, e A1 pode ter menos acesso aos ingressos.
- **(I, C) = (1, 2):** os controles elevam o custo de A2 e reduzem sua vantagem. A3 protege melhor o estoque, mas ainda suporta custo operacional e risco de atrasar ou bloquear A1.

Os números traduzem essas preferências relativas: para A2, capturar mais ingressos com baixo custo é melhor; para A3, preservar a distribuição justa sem atrito excessivo é melhor. Essa escolha de valores deve ser validada pelo grupo e pelo professor; alterar as preferências pode mudar o equilíbrio.

## Melhores respostas e estratégias dominantes

As melhores respostas podem ser identificadas comparando os payoffs de cada jogador, mantendo fixa a ação do outro:

- Se A3 **Permitir**, A2 prefere **Intensivo**: `4 > 3`.
- Se A3 **Controlar**, A2 prefere **Regular**: `2 > 1`.
- Se A2 escolher **Regular**, A3 prefere **Permitir**: `3 > 1`.
- Se A2 escolher **Intensivo**, A3 prefere **Controlar**: `2 > 0`.

Nenhum jogador possui estratégia dominante neste modelo: a melhor ação de cada um depende da ação escolhida pelo outro.

## Equilíbrio de Nash

Não há equilíbrio de Nash em estratégias puras nesta matriz. Em cada combinação, pelo menos um jogador pode melhorar seu payoff mudando unilateralmente de ação. Por exemplo, em (R, P), A2 melhora mudando para I; em (I, C), A2 melhora mudando para R.

Há um equilíbrio misto para os payoffs ilustrativos definidos acima. Seja `p` a probabilidade de A3 escolher Permitir e `q` a probabilidade de A2 escolher Regular.

- A2 fica indiferente entre R e I quando `2 + p = 1 + 3p`, logo `p = 1/2`.
- A3 fica indiferente entre P e C quando `3q = 2 - q`, logo `q = 1/2`.

Assim, no equilíbrio misto, A2 escolhe Regular com probabilidade de 1/2 e Intensivo com probabilidade de 1/2; A3 escolhe Permitir com probabilidade de 1/2 e Controlar com probabilidade de 1/2. Isso é uma propriedade matemática dos payoffs adotados, não uma previsão de que pessoas ou plataformas reais usarão essas frequências.

## Impacto e interpretação

O modelo mostra a tensão estratégica central. Se a plataforma não reforça os controles, a ação intensiva pode trazer maior retorno para A2 e prejudicar a distribuição justa. Se a plataforma controla, reduz a vantagem adversarial, mas também aumenta custos e atrito para compradores legítimos. Como A3 não sabe com certeza se está atendendo A1 ou A2, o controle pode gerar falsos positivos.

O equilíbrio misto indica que, sob estas preferências simplificadas, nenhuma das ações é sempre a melhor. A conclusão relevante não é aplicar controles aleatoriamente: é que as escolhas dependem dos incentivos e dos custos assumidos. Uma avaliação empírica ou outro conjunto de payoffs pode produzir resultados diferentes. A seção 3.3 amplia a análise ao mostrar como respostas observadas podem levar os jogadores a adaptar suas ações entre rodadas.

## Limitações

Este modelo comprime várias capacidades em apenas duas ações por jogador, usa payoffs ordinais hipotéticos e representa uma única rodada. Não estima probabilidades reais, valores de revenda, volume de estoque ou taxas de falso positivo. O comprador legítimo é considerado como afetado pelas decisões da plataforma, mas não aparece como terceiro jogador. Essas simplificações permitem analisar as melhores respostas e o equilíbrio sem confundir o modelo estático com o processo adaptativo da seção 3.3.
