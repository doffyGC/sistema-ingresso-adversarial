# 3.1 Descrição do sistema adversarial

> **Seção do enunciado:** 3.1 (Descrição do sistema adversarial)
> **Status:** rascunho para revisão do grupo

Este documento estabelece a **realidade compartilhada** sobre a qual as demais seções do
trabalho são construídas. As definições abaixo valem como vocabulário fixo: os jogadores
do modelo estático (3.2), os participantes das rodadas (3.3) e os ativos afetados pelas
ameaças (3.4) são exatamente os definidos aqui.

---

## 1. Delimitação da interação analisada

O sistema analisado é uma **plataforma de venda e reserva de ingressos para eventos**.
O trabalho **não analisa a plataforma inteira** — não tratamos de cadastro, catálogo de
eventos, emissão fiscal, check-in na portaria ou reembolso.

A interação delimitada é:

> **A tentativa de um comprador obter um ingresso para um evento de alta demanda,
> durante a janela de abertura das vendas, enquanto a plataforma aplica regras de
> controle de disponibilidade para distribuir um estoque finito.**

Concretamente, o recorte cobre um único fluxo, com três passos:

```text
[1] CONSULTAR          [2] RESERVAR                    [3] CONFIRMAR
disponibilidade   →    bloqueio temporário do    →     pagamento conclui
de um setor            ingresso por um prazo T         a compra, ou a
                       (reserva com TTL)               reserva expira e o
                                                       ingresso volta ao estoque
```

**Por que este recorte:** ele possui estoque finito e disputado, uma regra explícita que
pode ser explorada (a reserva temporária e os limites por identidade), resposta
observável a cada tentativa (sucesso, rejeição, fila, erro) e escopo pequeno o
suficiente para virar código no Trabalho 2.

### O que está dentro e fora do escopo

| Dentro do escopo | Fora do escopo |
|---|---|
| Consulta de disponibilidade de um setor | Catálogo e busca de eventos |
| Criação e expiração da reserva temporária | Emissão de nota fiscal e repasse ao organizador |
| Limites por identidade e por sessão | Check-in / validação do ingresso na portaria |
| Fila de espera e controle de ritmo de requisições | Política de reembolso e cancelamento |
| Confirmação de pagamento como evento que converte reserva em compra | Meios de pagamento e antifraude bancário |
| Revenda como **motivação** do adversário | O mercado secundário em si (fora da plataforma) |

---

## 2. Atores

Adotamos **três atores com poder de decisão**. A separação entre comprador legítimo e
comprador adversarial é deliberada: ela é o que permite, nas seções seguintes, discutir
**efeitos colaterais de uma defesa sobre usuários legítimos** — exigência explícita do
enunciado nas seções 3.3 e 3.4.

### A1 — Comprador legítimo

Pessoa física que quer um ou poucos ingressos para consumo próprio. Age manualmente,
pelo navegador ou aplicativo, dentro da janela de venda. É o usuário que o sistema
existe para servir e é ele quem paga o custo das defesas mal calibradas.

### A2 — Comprador adversarial (cambista / operador de bot)

Agente que busca **acumular ingressos acima do que consumiria**, para revender no
mercado secundário com sobrepreço. Possui capital, conhecimento técnico e disposição
para investir em infraestrutura. É **racional e adaptativo**: observa as respostas da
plataforma, infere as regras que não estão documentadas e ajusta a estratégia entre
tentativas e entre eventos.

### A3 — Plataforma de ingressos (defensor)

O sistema que media a interação. Decide quanto estoque expor, se aceita ou rejeita cada
reserva, por quanto tempo a reserva vale, quantos ingressos cada identidade pode obter e
quanto atrito impor a cada tentativa. Opera sob incerteza: **não sabe, no momento da
decisão, se quem está solicitando é A1 ou A2.**

### Atores de contexto (não modelados como jogadores)

- **Organizador do evento:** define preço, lotes e o tamanho do estoque. Pressiona pela
  venda rápida e integral, o que limita o quanto de atrito a plataforma pode impor.
- **Mercado secundário:** define o preço de revenda e, portanto, o retorno esperado de
  A2. Não toma decisão dentro do sistema, mas é a fonte do incentivo do adversário.

> **Nota:** o jogo estático da seção 3.2 deve ser modelado entre **A2 e A3**.
> A1 entra na análise como parte afetada (custo colateral), não como jogador da matriz.

---

## 3. Objetivos de cada ator

| Ator | Objetivo |
|---|---|
| **A1 — Comprador legítimo** | Obter o ingresso desejado com esforço e incerteza razoáveis, sem precisar de meios técnicos especiais |
| **A2 — Comprador adversarial** | Maximizar a quantidade de ingressos de alto valor capturados, minimizando o custo por ingresso e o risco de perder contas ou pedidos |
| **A3 — Plataforma** | Distribuir o estoque conforme as regras anunciadas, preservando justiça e disponibilidade, sem bloquear compradores legítimos nem inviabilizar a venda |

O conflito é **parcial, não total**: A2 e A3 concordam que os ingressos devem ser
vendidos; discordam sobre **quem** deve recebê-los e **a que custo**. A1 e A2 competem
diretamente pelo mesmo estoque finito. A1 e A3 têm objetivos alinhados, mas A3 não
consegue distinguir A1 de A2 com certeza — e é exatamente essa incerteza que A2 explora.

---

## 4. Ativo a ser preservado

**Ativo principal:**

> **A distribuição justa e controlada do estoque finito de ingressos** — isto é, a
> propriedade de que a alocação dos ingressos resulte das regras anunciadas pela
> plataforma, e não da capacidade técnica de automatizar tentativas.

Ativos secundários, derivados do principal:

| Ativo | O que significa neste sistema | Quem o ameaça |
|---|---|---|
| **Justiça da alocação** | O resultado reflete as regras anunciadas, não a assimetria técnica entre compradores | A2, ao converter capacidade computacional em vantagem de alocação |
| **Disponibilidade do estoque** | Ingressos não vendidos permanecem efetivamente acessíveis a quem quer comprar | A2, ao imobilizar estoque em reservas que não pretende pagar |
| **Integridade das reservas** | Uma reserva corresponde a exatamente um ingresso, e expira quando deve | Condições de corrida exploradas deliberadamente |
| **Confiança no processo** | O comprador acredita que tentar vale a pena | Ambos: A2 ao esvaziar o estoque, A3 ao impor atrito excessivo |

> **Não confundir:** a plataforma é **ator**; o estoque de ingressos é **recurso**; a
> *justiça da distribuição desse estoque* é o **ativo**. O cambista é **ator**, não
> ameaça; o que ele faz (acumular via automação) é a **ameaça** — detalhada na seção 3.4.

---

## 5. Ações e capacidades

### A1 — Comprador legítimo

- Consultar a disponibilidade de um setor do evento
- Selecionar setor e quantidade
- Solicitar uma reserva temporária
- Concluir o pagamento dentro do prazo da reserva
- Repetir a tentativa após uma rejeição (manualmente, poucas vezes)
- Aguardar em fila de espera, se houver
- Desistir

### A2 — Comprador adversarial

Possui **todas** as capacidades de A1, e adicionalmente:

- **Automatizar** as requisições, eliminando o tempo de reação humano
- **Paralelizar** dezenas ou centenas de sessões simultâneas
- **Multiplicar identidades**: criar ou adquirir contas, usar documentos de terceiros
- **Rotacionar origem**: trocar IP, dispositivo e *fingerprint* entre tentativas
- **Monitorar** o endpoint de disponibilidade em alta frequência, detectando a abertura
  do lote antes de qualquer humano
- **Imobilizar estoque**: abrir muitas reservas e deixá-las expirar, ou renová-las,
  retirando ingressos de circulação sem pagar por eles
- **Calibrar o comportamento** para se parecer com tráfego humano (intervalos irregulares)
- **Terceirizar** a resolução de CAPTCHA
- Revender os ingressos obtidos fora da plataforma

### A3 — Plataforma

- Publicar (ou omitir) a disponibilidade de cada setor
- Aceitar ou rejeitar uma solicitação de reserva
- Definir o prazo de validade (TTL) da reserva
- Liberar automaticamente as reservas expiradas
- Limitar a quantidade de ingressos por identidade
- Limitar o ritmo de requisições por sessão, conta ou origem (*rate limiting*)
- Inserir uma fila de espera com ordenação
- Exigir prova de humanidade (CAPTCHA) ou verificação de identidade
- Registrar telemetria de comportamento de cada sessão
- Cancelar pedidos e suspender contas *a posteriori*
- Escolher **o que comunicar** ao usuário em cada rejeição

> A última capacidade é a mais sutil e a mais importante para a seção 3.3: **toda
> resposta da plataforma é também um sinal**, e escolher a mensagem de erro é escolher
> quanta informação entregar ao adversário.

---

## 6. Informações observáveis

O que cada ator **consegue** e **não consegue** observar define o que ele pode aprender
entre uma rodada e a seguinte.

### A1 — Comprador legítimo observa

- A disponibilidade exibida na tela
- O resultado da sua tentativa (aceita, rejeitada, em fila)
- A mensagem de erro apresentada
- A posição na fila e o tempo estimado de espera
- O tempo restante da sua reserva

**Não observa:** o estoque real, quantos concorrentes existem, nem por que foi rejeitado.

### A2 — Comprador adversarial observa

Tudo o que A1 observa, e ainda:

- **Códigos de status e latência** de cada resposta — e a diferença entre elas
- **Qual das suas contas ou IPs foi bloqueado, e após quantas tentativas** — o que revela
  a ordem de grandeza dos limiares de detecção
- O **instante exato** em que o estoque muda, por amostragem de alta frequência
- A **taxa de sucesso de cada estratégia**, medida sobre muitas tentativas
- Se uma rejeição é determinística ou probabilística (repetindo a mesma requisição)
- O comportamento do sistema em **eventos anteriores**, acumulado entre vendas

**Não observa:** o código das regras de detecção, os limiares exatos, quais sessões foram
silenciosamente marcadas como suspeitas, nem o estoque real.

### A3 — Plataforma observa

- Volume, frequência e intervalo entre requisições por sessão, conta e origem
- Cabeçalhos, *fingerprint* de dispositivo e origem de rede
- Histórico de reservas por identidade
- A **taxa de conversão reserva → pagamento** de cada identidade — o indicador mais
  revelador de imobilização de estoque
- Correlações entre contas (mesmo meio de pagamento, mesmo dispositivo)

**Não observa:** a pessoa real por trás de uma conta, a intenção da compra, e — antes do
prazo da reserva expirar — se aquela reserva será paga. A plataforma **decide sob
incerteza e sob pressão de tempo**.

> **Assimetria central do sistema:** A2 observa o *resultado* das regras de A3 e pode
> inferir as regras. A3 observa o *comportamento* de A2, mas não sua identidade nem sua
> intenção. Nenhum lado enxerga o outro por completo, e ambos aprendem com o que veem.

---

## 7. Restrições e custos

| Ator | Restrições e custos |
|---|---|
| **A1** | Estoque finito; prazo curto para pagar; limite de ingressos por identidade; precisa estar disponível no horário exato da abertura; tolerância limitada a atrito (CAPTCHA, fila, erros) antes de desistir; custo emocional da frustração |
| **A2** | Custo de infraestrutura (servidores, proxies, contas, resolução de CAPTCHA); custo de aquisição e risco de perda de identidades ao serem banidas; capital imobilizado nos ingressos até a revenda; janela temporal estreita (o lote esgota em minutos); risco de cancelamento *a posteriori* do pedido; custo crescente se a plataforma exigir verificação de identidade |
| **A3** | Capacidade computacional sob pico de carga; **custo de falso positivo** — bloquear um comprador legítimo é caro em reputação e em receita; latência aceitável (atrito demais derruba a conversão); pressão do organizador por venda rápida e integral; custo de operação e moderação manual; exposição regulatória e de imagem se a venda for percebida como injusta |

> A restrição decisiva é a de A3: **ela não pode simplesmente maximizar a segurança.**
> Toda defesa que dificulta a vida de A2 também impõe custo a A1, e o orçamento de
> atrito que A1 tolera é pequeno. É essa tensão que torna o problema estratégico em vez
> de puramente técnico.

---

## 8. Tabela consolidada dos elementos principais

| Ator | Objetivo | Ações ou capacidades | Informações observáveis | Restrições ou custos |
|---|---|---|---|---|
| **A1 — Comprador legítimo** | Obter o ingresso desejado com esforço razoável | Consultar, selecionar, reservar, pagar, reenviar tentativa manual, aguardar na fila, desistir | Disponibilidade exibida, resultado da tentativa, mensagem de erro, posição na fila, TTL restante | Estoque finito, prazo curto de pagamento, limite por identidade, precisa estar online no horário, baixa tolerância a atrito |
| **A2 — Comprador adversarial** | Capturar o máximo de ingressos de alto valor ao menor custo e risco | Tudo de A1 + automação, paralelismo, múltiplas identidades, rotação de IP/dispositivo, monitoramento de alta frequência, imobilização de estoque, imitação de tráfego humano, terceirização de CAPTCHA | Tudo de A1 + latência e códigos de resposta, qual identidade caiu e após quantas tentativas, instante da liberação do lote, taxa de sucesso por estratégia, histórico entre eventos | Custo de infraestrutura e de contas, risco de banimento e de cancelamento do pedido, capital imobilizado, janela temporal estreita, custo de KYC |
| **A3 — Plataforma** | Distribuir o estoque conforme as regras anunciadas, preservando justiça e disponibilidade | Publicar disponibilidade, aceitar/rejeitar reserva, definir e aplicar TTL, liberar expiradas, limitar por identidade, *rate limiting*, fila de espera, CAPTCHA/verificação, telemetria, cancelar e suspender, escolher a mensagem de resposta | Volume e cadência de requisições, *fingerprint* e origem, histórico de reservas, taxa de conversão reserva→pagamento, correlação entre contas | Capacidade sob pico, custo alto de falso positivo, latência aceitável, pressão do organizador por venda rápida, custo de moderação, exposição reputacional |

---

## 9. Pressupostos do sistema e como podem falhar

O enunciado exige pelo menos dois pressupostos. Listamos cinco, porque cada um deles vira
um ponto de exploração rastreável na seção 3.4. **Um pressuposto é uma afirmação que o
sistema trata como verdadeira sem verificar.**

### P1 — Uma identidade corresponde a uma pessoa

O limite de ingressos por comprador só funciona se cada conta (ou CPF) representar um ser
humano distinto.

**Como falha:** contas criadas em massa com e-mails descartáveis; uso de documentos de
terceiros (familiares, laranjas); compra de contas antigas e "aquecidas". Quando P1 cai,
o limite por identidade deixa de limitar qualquer coisa — ele apenas define quantas
contas o adversário precisa manter.

### P2 — Uma reserva não paga é devolvida ao estoque e beneficia outro comprador

O TTL da reserva existe para que estoque bloqueado volte a circular.

**Como falha:** o adversário abre reservas em massa **sem intenção de pagar**, e as deixa
expirar ou as renova em ciclo. O estoque volta ao pool, mas volta para quem está
monitorando em alta frequência — ou seja, para o próprio adversário. O mecanismo
projetado para proteger a disponibilidade vira uma ferramenta de **negação de serviço
sobre o estoque**, e o comprador legítimo vê a disponibilidade oscilar e conclui que
"esgotou".

### P3 — A cadência e o volume de requisições revelam se o agente é humano

A detecção comportamental pressupõe que tráfego automatizado é estatisticamente distinto
de tráfego humano.

**Como falha:** nos dois sentidos. O adversário insere atrasos irregulares e imita
padrões humanos, ficando abaixo do limiar (**falso negativo**). E, no pico da abertura das
vendas, o comprador legítimo ansioso recarrega a página compulsivamente e **parece um
bot** (**falso positivo**). O limiar que separa os dois casos não existe de forma limpa.

### P4 — A disponibilidade exibida é a mesma para todos e reflete o estoque real

**Como falha:** por razões de desempenho, a disponibilidade é servida de cache ou de
réplicas, com atraso de propagação. Compradores diferentes veem números diferentes no
mesmo instante. Quem consulta a API diretamente, sem passar pela interface, enxerga o
lote **antes** de quem usa o site — vantagem que não foi concedida por nenhuma regra
anunciada.

### P5 — O custo de uma tentativa é semelhante para todos os compradores

A ideia implícita de "quem chegar primeiro leva" pressupõe uma disputa entre agentes com
capacidades comparáveis.

**Como falha:** para A1, cada tentativa custa atenção, tempo e desgaste; para A2, o custo
marginal de mais uma tentativa é praticamente zero. A mesma regra, aplicada igualmente
aos dois, produz resultados radicalmente desiguais. **Tratamento igual não produz
resultado justo quando as capacidades são assimétricas.**

### Resumo dos pressupostos

| ID | Pressuposto | Modo de falha | Ativo colocado em risco |
|---|---|---|---|
| **P1** | Uma identidade = uma pessoa | Contas em massa, documentos de terceiros, contas compradas | Justiça da alocação |
| **P2** | Reserva não paga volta a circular para outro comprador | Imobilização deliberada de estoque via reservas sem intenção de pagar | Disponibilidade do estoque |
| **P3** | Cadência de requisições distingue humano de bot | Automação que imita humano; humano em pico que parece bot | Justiça da alocação e confiança |
| **P4** | A disponibilidade exibida é única e fiel | Cache e réplicas com atraso; acesso direto à API | Justiça da alocação |
| **P5** | O custo de tentar é semelhante para todos | Automação zera o custo marginal da tentativa para o adversário | Justiça da alocação |

> **Entrega para a seção 3.4:** estes cinco pressupostos são os candidatos naturais a
> pontos de exploração da superfície de ataque. Cada um já vem com o ativo afetado.

---
