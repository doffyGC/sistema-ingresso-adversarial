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
