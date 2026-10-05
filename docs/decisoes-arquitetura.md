# Decisões de arquitetura futura

Este complemento transforma os controles R1–R6 de [`resiliencia.md`](resiliencia.md) em
decisões verificáveis para o Trabalho 2. Ele não escolhe linguagem ou *framework*: fixa
regras que devem sempre ser verdadeiras, responsabilidades e comportamento sob falha.

## Invariantes do domínio

| ID | Invariante | Como verificar no Trabalho 2 |
|---|---|---|
| **INV1** | Um ingresso ocupa exatamente um estado: `DISPONIVEL`, `RESERVADO`, `OFERTADO_FILA` ou `VENDIDO` | Teste automatizado após toda transição e consulta ao estoque dentro da mesma transação |
| **INV2** | No máximo uma reserva ativa referencia o mesmo ingresso | Restrição única no armazenamento e teste com reservas concorrentes |
| **INV3** | Uma identidade ou cluster não ultrapassa o limite de reservas ativas | Duas tentativas paralelas devem produzir uma aceitação e uma rejeição que possa ser repetida sem criar novo efeito |
| **INV4** | Ingresso expirado é oferecido à fila antes de voltar ao estoque público | Teste que monitora F1 durante `RESERVADO → OFERTADO_FILA` |
| **INV5** | Toda oferta à fila possui prazo; nenhum ingresso fica retido indefinidamente | Relógio simulado e teste de progresso até `RESERVADO` ou `DISPONIVEL` |
| **INV6** | Repetir a mesma requisição não cria outra reserva ou cobrança | Chave de idempotência e repetição do pedido sob falha de rede |
| **INV7** | Cancelamento de alto impacto mantém evidência, política aplicada e caminho de contestação | Auditoria do evento e teste do fluxo de revisão |

INV1–INV6 preservam disponibilidade e integridade mesmo se o Detector estiver indisponível.
O componente analítico melhora a decisão, mas não pode ser requisito para o estoque
continuar consistente.

## Registros de decisão

### DA1: redistribuir pela fila antes do estoque público

- **Decisão:** ao expirar, o ingresso passa para `OFERTADO_FILA`; somente volta a
  `DISPONIVEL` quando a fila termina.
- **Razão:** fecha PE3 e quebra a cadeia T1 sem exigir identificar A2.
- **Alternativa rejeitada:** reduzir apenas o TTL. Isso encurta a retenção, mas mantém a
  recaptura por quem monitora F1.
- **Custo:** quem esperava capturar uma devolução pública passa a depender da fila.

### DA2: controle central do estado do ingresso

- **Decisão:** Reserva, Expiração e Redistribuição solicitam mudanças de estado a um único
  componente responsável pelo estoque. Cada mudança é concluída por inteiro ou não é
  realizada.
- **Razão:** impede que componentes concorrentes vendam, expirem ou ofereçam o mesmo
  ingresso simultaneamente.
- **Alternativa rejeitada:** cada componente gravar diretamente no banco. Isso amplia as
  janelas de corrida de PE5.
- **Custo:** o serviço de estoque precisa de alta disponibilidade e controle explícito de
  concorrência.

### DA3: repetição segura em reserva, pagamento e expiração

- **Decisão:** cada operação aceita uma chave única e grava o resultado associado.
- **Razão:** a repetição causada por tempo de espera excedido não pode parecer uma nova
  ação adversarial nem gerar outra reserva ou cobrança. Essa repetição segura é chamada
  de idempotência.
- **Alternativa rejeitada:** deduplicar somente pelo instante da requisição, pois tentativas
  legítimas próximas podem ser confundidas.
- **Custo:** armazenamento temporário de chaves e definição do prazo de retenção.

### DA4: o Detector recomenda e o estoque preserva suas regras

- **Decisão:** o Detector marca risco e sugere R5/R6, mas não altera diretamente o estoque.
- **Razão:** uma classificação errada não pode corromper o ciclo de vida do ingresso.
- **Alternativa rejeitada:** bloqueio automático por um único limiar; aumenta falsos
  positivos e fornece um oráculo a T3.
- **Custo:** decisões graves podem exigir moderação e chegar mais tarde.

### DA5: respostas externas estáveis e auditoria interna detalhada

- **Decisão:** F7 usa categorias genéricas; internamente, a decisão registra sinais,
  versão da política e controle acionado.
- **Razão:** reduz a calibragem de T3 sem impedir diagnóstico e contestação por A1.
- **Alternativa rejeitada:** esconder também o motivo internamente, pois inviabiliza medir
  falsos positivos.
- **Custo:** suporte precisa consultar a trilha de auditoria para explicar a decisão em um
  canal autenticado.

## Comportamento sob falha

| Falha | Comportamento seguro | Degradação aceita | O que não pode acontecer |
|---|---|---|---|
| Detector indisponível | Manter fila, limites por identidade, TTL e invariantes do estoque | Suspender R5 e encaminhar casos de R6 para revisão | Liberar reservas ilimitadas ou cancelar automaticamente |
| Pagamento indisponível | Não confirmar venda; conservar a reserva até o limite previsto | Permitir uma única prorrogação registrada | Cobrar duas vezes ou manter reserva indefinidamente |
| Fila indisponível | Pausar novas admissões e preservar estados existentes | Exibir indisponibilidade temporária | Devolver todo ingresso expirado ao estoque público e reabrir T1 |
| Telemetria indisponível | Continuar o fluxo transacional e armazenar eventos localmente para reenvio | Painel temporariamente defasado | Descartar silenciosamente decisões de alto impacto |
| Moderação indisponível | Adiar cancelamentos *a posteriori* | Aumentar o tempo de resposta | Cancelar pedido legítimo sem revisão nem contestação |

## Critérios de aceite do protótipo

1. Em cem tentativas concorrentes para o mesmo ingresso, exatamente uma reserva é criada.
2. Repetir a mesma chave de idempotência retorna o mesmo resultado sem novo efeito.
3. Uma reserva expirada nunca reaparece em F1 enquanto houver comprador elegível na fila.
4. A segunda reserva ativa do mesmo cluster é rejeitada sem revelar qual limiar disparou.
5. Falha simulada do Detector não viola INV1–INV6.
6. O painel apresenta conversão, estoque retido, periodicidade, desistência de A1 e
   contestações por versão da política.
7. Um cancelamento registra evidência e pode ser revertido por contestação.

Esses critérios tornam a arquitetura implementável e permitem demonstrar no Trabalho 2
que a resposta reduz T1 sem apresentar a defesa como solução definitiva.

