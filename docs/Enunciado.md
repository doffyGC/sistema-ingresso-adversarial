# Trabalho 1 - Análise de um Sistema Adversarial

## Modelo estático, modelo dinâmico, ameaças e riscos

> **Modalidade:** grupos de 4 a 6 estudantes  
> **Prazo:** 06/10 às 23:59
> **Entrega:** repositório Git contendo o relatório principal em Markdown + apresentação em slides (submeter o link da apresentação em PDF, ex. Google Drive).
> **Vídeo de Apresentação com Slides:** deve ser entregue um vídeo gravado preferencialmente na plataforma CANVA e disponibilizado por meio do YouTube. Discentes do PPGES terão seus vídeos executados ao vivo e poderão responder perguntas em seguida. Os da graduação deverão responder questões de forma assíncrona conforme for solicitado pelos professores.

## 1\. Proposta

O grupo deverá escolher e descrever um sistema de software no qual diferentes participantes possam possuir **objetivos conflitantes**, tomar decisões e adaptar seu comportamento a partir das respostas observadas.

O trabalho deverá responder à seguinte questão:

> **O que torna esse sistema adversarial, como os participantes tomam decisões e como a interação evolui ao longo das rodadas?**

O objetivo não é executar ataques nem construir uma solução completa. O grupo deverá produzir uma análise clara, concreta e coerente, aplicando os conceitos estudados em quatro partes:

1. descrição do sistema adversarial;
2. modelo estratégico estático;
3. modelo estratégico dinâmico;
4. ameaças e riscos.

> **Continuidade com o Trabalho 2:** este trabalho corresponde à etapa de **planejamento e desenho arquitetural**. O sistema descrito no Trabalho 1 será utilizado como base para o **Trabalho 2**, no qual a proposta deverá ser transformada em código. Por isso, as decisões apresentadas agora deverão ser concretas, coerentes e viáveis de implementar posteriormente.

## 2\. Escolha do sistema

O grupo poderá analisar um sistema existente ou propor um novo sistema. São exemplos:

* plataforma de avaliações;
* venda ou reserva de ingressos;
* sistema de promoções e recompensas;
* agendamento de serviços;
* marketplace ou aplicativo de entregas;
* ranking acadêmico ou profissional;
* rede social ou sistema de moderação;
* outro sistema aprovado pelos professores.

Não analisem um domínio inteiro, como “rede social”, “banco” ou “sistema acadêmico”. Escolham **uma interação específica**, como publicar uma avaliação, comprar um ingresso, reservar um horário ou receber uma recompensa.

O caso escolhido deverá possuir:

* pelo menos dois participantes capazes de tomar decisões;
* objetivos total ou parcialmente conflitantes;
* uma regra, métrica ou decisão que possa ser explorada;
* alguma resposta observável que permita reação ou adaptação;
* escopo suficientemente pequeno para ser implementado no Trabalho 2.

## 3\. Desenvolvimento

### 3.1 Descrição do sistema adversarial

Descrevam:

* qual é o sistema e qual interação será analisada;
* quais são os principais atores;
* qual é o objetivo de cada ator;
* qual ativo ou propriedade precisa ser preservado, como justiça, confiança, privacidade, disponibilidade ou distribuição correta de um recurso;
* quais ações ou capacidades cada ator possui;
* quais informações cada ator consegue observar;
* quais custos ou restrições limitam suas ações;
* pelo menos dois pressupostos dos quais o sistema depende;
* como esses pressupostos podem falhar.

Organizem os elementos principais em uma tabela:

|Ator|Objetivo|Ações ou capacidades|Informações observáveis|Restrições ou custos|
|-|-|-|-|-|
|Ator 1|||||
|Ator 2|||||

Incluam um **diagrama de contexto** simples, mostrando o sistema, os participantes e suas principais interações.

Finalizem esta parte explicando por que o caso representa uma situação adversarial, e não apenas um erro ou acidente.

### 3.2 Modelo estratégico estático

Modelem uma decisão central como um jogo com dois jogadores e duas ações possíveis para cada um.

|Jogador A \\ Jogador B|Ação B1|Ação B2|
|-|-:|-:|
|**Ação A1**|`( , )`|`( , )`|
|**Ação A2**|`( , )`|`( , )`|

Utilizem valores simples, como 0, 1, 2 e 3, para representar a ordem de preferência de cada jogador. Informem a ordem utilizada no par, por exemplo: `(payoff de A, payoff de B)`.

Após a matriz, expliquem:

1. o que representa cada ação;
2. por que cada resultado recebeu aqueles payoffs;
3. quais são as melhores respostas dos jogadores;
4. se existe estratégia dominante;
5. se existe um resultado no qual nenhum jogador melhora mudando sozinho;
6. se esse resultado é bom para o sistema e para os usuários legítimos.

Não é obrigatório existir estratégia dominante ou um único equilíbrio. O importante é demonstrar que a melhor decisão depende da escolha do outro participante.

### 3.3 Modelo estratégico dinâmico

Transformem a análise anterior de uma “fotografia” em um “filme”. Representem pelo menos **três rodadas adversariais** seguindo o ciclo:

> **ação → resposta → observação → adaptação**

|Rodada|Ação do participante|Resposta do sistema ou defensor|O que se torna observável?|Adaptação para a rodada seguinte|
|-:|-|-|-|-|
|1|||||
|2|||||
|3|||||

As rodadas deverão mostrar que:

* a resposta do sistema também produz informação;
* o participante pode manter o mesmo objetivo e mudar sua ação;
* o defensor também pode observar e adaptar sua resposta;
* decisões passadas alteram as possibilidades das rodadas seguintes;
* uma defesa pode produzir custos ou dificuldades para usuários legítimos.

Incluam um **diagrama do ciclo adaptativo**, representando visualmente as rodadas.

Ao final, respondam brevemente:

* quem observa quem?;
* o que cada lado consegue mudar?;
* o que dispara uma adaptação?;
* qual é o custo da adaptação para cada lado?;
* em que ponto pode surgir uma corrida armamentista?

### 3.4 Ameaças e riscos

Identifiquem pelo menos **três pontos de exploração** presentes no sistema ou nas rodadas modeladas. Representem esses pontos em um **diagrama de superfície de ataque**, indicando interfaces, regras, componentes ou fluxos envolvidos.

A partir desses pontos, descrevam pelo menos **três cenários de ameaça**.

Utilizem o seguinte formato:

> Um **[ator]** pode realizar **[ação]** por meio de **[ponto de exploração]**, aproveitando **[fraqueza ou pressuposto]**, causando **[impacto]** sobre **[ativo ou propriedade]**.

Avaliem os riscos utilizando uma escala simples de 1 a 3:

* **probabilidade:** 1 = baixa, 2 = média, 3 = alta;
* **impacto:** 1 = baixo, 2 = médio, 3 = alto;
* **risco:** probabilidade × impacto.

|ID|Cenário de ameaça|Ponto de exploração|Pressuposto ou fraqueza|Ativo afetado|Probabilidade|Impacto|Risco|
|-|-|-|-|-|-:|-:|-:|
|A1||||||||
|A2||||||||
|A3||||||||

Escolham a ameaça de maior prioridade e expliquem:

1. como o sistema poderia responder;
2. que informação essa resposta revelaria;
3. como o adversário poderia se adaptar na rodada seguinte;
4. quais efeitos colaterais poderiam atingir usuários legítimos;
5. qual risco continuaria existindo após a resposta;
6. o que o sistema precisa continuar preservando apesar das adaptações.

## 4\. Entregáveis

O repositório deverá seguir, no mínimo, esta organização:

```text
trabalho-adversarial/
├── README.md
├── diagramas/
│   ├── contexto.png
│   ├── superficie-de-ataque.png
│   └── ciclo-adaptativo.png
└── fontes/
    └── referencias.md
```

O arquivo `README.md` será o relatório principal e deverá permitir a compreensão do trabalho sem consulta a arquivos externos não referenciados.

Diagramas poderão ser produzidos em Mermaid, PlantUML, draw.io ou ferramenta equivalente. Quando uma ferramenta visual for utilizada, entreguem também o arquivo-fonte editável.

Nesta etapa, **não será exigida implementação de código**. A entrega deverá se concentrar no planejamento, na modelagem estratégica, na análise de ameaças e no desenho arquitetural do sistema.

No **Trabalho 2**, o grupo deverá transformar esta descrição em uma implementação funcional. O Trabalho 1 funcionará, portanto, como especificação e base arquitetural para o desenvolvimento posterior. Código produzido antecipadamente não substitui nenhum dos artefatos exigidos nesta etapa.

## 5\. Critérios de avaliação

|Critério|Pontos|O que será observado|
|-|-:|-|
|Delimitação e fundamentos adversariais|15|Recorte claro, conflito, atores, ativos, capacidades, restrições e pressupostos|
|Modelo estratégico estático|20|Coerência dos jogadores, ações, payoffs, melhores respostas e equilíbrios|
|Modelo estratégico dinâmico|20|Qualidade do ciclo ação-resposta-observação-adaptação, custos e efeitos colaterais|
|Superfície e cenários de ameaça|25|Rastreabilidade entre arquitetura, superfícies, pressupostos, ameaças, ativos e impactos|
|Redesenho e resiliência|15|Controles contextualizados, mudança de incentivos, observabilidade, adaptação e risco residual|
|Clareza, evidências e organização|5|Qualidade do Markdown, diagramas, referências, consistência e histórico de contribuições|
|**Total**|**100**||

> Todos os critérios dependem da qualidade de sua apresentação. Não basta entregar. Também é necessário demonstrar balanço entre a fala de cada integrante do grupo, além de balanço na contribuição no github (medida por commits individuais). Isto significa que a nota não é única para o grupo, podendo haver discrepância significativa entre os membros mais atuantes e os demais.

### 5.1 O que reduz a qualidade da análise

* descrever um sistema amplo sem delimitar uma interação;
* tratar todo erro como ação adversarial;
* confundir ator, ativo, ameaça, vulnerabilidade e impacto;
* usar payoffs arbitrários sem justificar preferências;
* marcar um equilíbrio sem analisar as melhores respostas;
* apresentar rodadas desconectadas, sem mostrar observação e adaptação;
* listar ameaças genéricas que não aparecem no sistema analisado;
* apresentar uma defesa como solução definitiva e ignorar a reação seguinte.

## 6\. Orientações finais

* Todas as fontes externas deverão ser referenciadas.
* O uso de IA generativa deverá ser declarado no final do relatório, indicando para quais tarefas foi utilizada e como o grupo verificou o conteúdo produzido.
* Cada integrante deverá possuir contribuições identificáveis no histórico do repositório.
* O grupo deverá compreender e conseguir explicar todas as decisões apresentadas.
* Não realizem testes invasivos em sistemas reais sem autorização formal.
* Utilizem documentação pública, exemplos hipotéticos, dados sintéticos ou ambientes próprios.

Antes da entrega, verifiquem se o trabalho apresenta:

* \[ ] uma interação específica e bem delimitada;
* \[ ] atores, objetivos, ativos, capacidades, informações e pressupostos;
* \[ ] uma matriz de payoffs explicada;
* \[ ] pelo menos três rodadas de ação, resposta, observação e adaptação;
* \[ ] os três diagramas solicitados;
* \[ ] pelo menos três ameaças ligadas ao sistema analisado;
* \[ ] avaliação de probabilidade, impacto e risco;
* \[ ] resposta à ameaça prioritária, próxima adaptação e risco residual;
* \[ ] referências, declaração de uso de IA e contribuições individuais.

## 7\. Pergunta final

> **Depois que o sistema responder, o que o outro lado aprenderá e tentará fazer em seguida?**