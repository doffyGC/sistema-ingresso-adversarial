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
