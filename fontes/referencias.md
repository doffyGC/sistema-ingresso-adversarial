# Referências

> Arquivo colaborativo. As fontes de cada seção entram sob o cabeçalho correspondente,
> mantendo a numeração contínua e o padrão de formatação abaixo.
> A conferência final e a padronização são tarefa coletiva antes da entrega.

**Padrão adotado:** AUTOR/INSTITUIÇÃO. *Título*. Edição/Publicação, ano. Disponível em:
`<url>`. Acesso em: dd/mm/aaaa.

**Formato dos diagramas.** Cada figura é entregue em três arquivos: o **arquivo-fonte
editável** (`.mmd` para Mermaid, board do FigJam para os diagramas de contexto), o `.svg`
e o `.png`. As exceções são o ciclo adaptativo (Fig. 3) e a superfície de ataque (Fig. 4): a fonte editável de cada uma é um arquivo do Figma, e a figura é entregue só em `.png`, exportado dele. Os documentos referenciam o `.png`, porque o SVG gerado pelo Mermaid guarda
os rótulos de texto em `foreignObject`, que os navegadores não renderizam quando o SVG é
embutido como imagem — no GitHub, a figura apareceria sem nenhum texto.

---

## Seção 3.1 — Descrição do sistema adversarial

1. **ESTADOS UNIDOS.** *Better Online Ticket Sales Act of 2016 (BOTS Act)*. Public Law
   114-274, 14 dez. 2016. Disponível em:
   `https://www.congress.gov/bill/114th-congress/senate-bill/3183`. Acesso em: 05/10/2026.
   Fonte primária que caracteriza legalmente a burla de medidas de controle de
   aquisição em plataformas de venda de ingressos. Sustenta o pressuposto **P1**
   (uma identidade corresponde a uma pessoa) e a caracterização do ator **A2**.

2. **FEDERAL TRADE COMMISSION (FTC).** *FTC Brings First-Ever Cases Under the BOTS Act*.
   Comunicado de imprensa, 22 jan. 2021. Disponível em:
   `https://www.ftc.gov/news-events/news/press-releases/2021/01/ftc-brings-first-ever-cases-under-bots-act`.
   Acesso em: 05/10/2026. Primeira ação de fiscalização sob o BOTS Act: três revendedores
   de Nova York adquiriram mais de 150 mil ingressos usando software de compra
   automatizada, ocultação de endereço IP e **centenas de contas e cartões fictícios para
   contornar o limite por comprador**. É a evidência empírica de que os pressupostos **P1**
   (uma identidade é uma pessoa) e **P3** (a cadência distingue humano de bot) falham na
   prática, e de que o mercado secundário sustenta o incentivo econômico de **A2**.

3. **OWASP FOUNDATION.** *OWASP Automated Threats to Web Applications* (catálogo OAT).
   Disponível em: `https://owasp.org/www-project-automated-threats-to-web-applications/`.
   Acesso em: 05/10/2026. Categorias utilizadas: **OAT-021 Denial of Inventory** (base do pressuposto **P2**),
   **OAT-019 Account Creation** (base de **P1**) e **OAT-006 Expediting** (base de **P5**).

4. **ANDERSON, Ross.** *Security Engineering: A Guide to Building Dependable Distributed
   Systems*. 3. ed. Indianapolis: Wiley, 2020. Economia da segurança e assimetria de
   custos entre atacante e defensor; sustenta a seção 7 (restrições e custos) e o
   pressuposto **P5**.

### Ferramentas utilizadas nesta seção

- **FigJam (Figma)** — produção dos diagramas de contexto. **Arquivo-fonte editável:**
  board do grupo em `https://www.figma.com/board/57yNrenUGK0zE7HpL4JfO3`.
  Exportado para `diagramas/contexto.svg` (Fig. 1, DFD nível 0),
  `diagramas/contexto-fluxo.svg` (Fig. 2) e `diagramas/contexto-legenda.svg`, e também
  em `.png`, que é a versão referenciada nos documentos.

### Ferramentas de IA generativa utilizadas nesta seção

- **ChatGPT (OpenAI)** — *brainstorming* da escolha do sistema e do recorte da interação.
- **Claude (Anthropic)** — apoio à redação e estruturação da seção 3.1.

---

## Seção 3.2 — Modelo estratégico estático

5. **OSBORNE, Martin J.; RUBINSTEIN, Ariel.** *A Course in Game Theory*. Cambridge, MA:
   MIT Press, 1994. Fundamenta o método da seção: jogo em forma normal, melhores
   respostas, estratégia dominante, equilíbrio de Nash em estratégias puras e o cálculo
   do equilíbrio em estratégias mistas pela condição de indiferença (`p = 1/2`,
   `q = 1/2`).

6. **SHOHAM, Yoav; LEYTON-BROWN, Kevin.** *Multiagent Systems: Algorithmic,
   Game-Theoretic, and Logical Foundations*. Cambridge: Cambridge University Press,
   2009. Uso de jogos 2×2 com payoffs ordinais para modelar agentes computacionais que
   decidem sob conflito; sustenta a escolha de uma escala ordinal ilustrativa em vez de
   valores monetários.

### Ferramentas de IA generativa utilizadas nesta seção

- **ChatGPT (OpenAI)** — apoio à redação e estruturação da matriz, da justificativa dos
  payoffs e da análise de equilíbrio da seção 3.2.

## Seção 3.3 — Modelo estratégico dinâmico

- Reutiliza a referência **3** (OWASP OAT): **OAT-021 Denial of Inventory** sustenta a
  imobilização de estoque da rodada 3.

### Ferramentas utilizadas nesta seção

- **Figma**: diagrama do ciclo adaptativo. Fonte editável em `https://www.figma.com/design/q2NAClihvDD5Txs2FhkKdm/Ciclo-Adaptativo?node-id=3-2`, exportado para `diagramas/ciclo-adaptativo.png`.

### Ferramentas de IA generativa utilizadas nesta seção

- **Claude (Anthropic)** — apoio à redação e estruturação da seção 3.3.

## Seção 3.4 — Superfície de ataque

- Reutiliza a referência **3** (OWASP OAT): **OAT-021 Denial of Inventory** sustenta PE2 e PE3, **OAT-019 Account Creation** sustenta PE4 e PE8, e **OAT-006 Expediting** sustenta PE1.

7. **OWASP FOUNDATION.** *Attack Surface Analysis Cheat Sheet*. OWASP Cheat Sheet Series. Disponível em: `https://cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html`. Acesso em: 05/10/2026. Base do método usado: enumerar pontos de entrada e saída, separar o que é controlado pelo cliente e rever a superfície a cada mudança no sistema.

8. **MITRE.** *CWE-367: Time-of-check Time-of-use (TOCTOU) Race Condition*. Common Weakness Enumeration. Disponível em: `https://cwe.mitre.org/data/definitions/367.html`. Acesso em: 05/10/2026. Caracteriza a fraqueza de implementação de PE5 (verificar o limite e gravar a reserva sem atomicidade).

### Ferramentas utilizadas nesta seção

- **Figma**: diagrama de superfície de ataque. Fonte editável em `https://www.figma.com/design/nq9MDoLrefjunzNgOmu31n/Arquivo?node-id=51-2`, exportado para `diagramas/superficie-de-ataque.png`.

### Ferramentas de IA generativa utilizadas nesta seção

- **Claude (Anthropic)**: apoio à redação e estruturação dos pontos de exploração, das tabelas de rastreabilidade e do diagrama de superfície de ataque.

## Seção 3.4 — Cenários de ameaça

- Reutiliza a referência **3** (OWASP OAT): **OAT-021 Denial of Inventory** caracteriza T1 e
  **OAT-019 Account Creation**, T2.
- Reutiliza a referência **8** (MITRE CWE-367): caracteriza a parte de T2 que explora a
  verificação do limite sem atomicidade (PE5).

### Ferramentas de IA generativa utilizadas nesta seção

- **Claude (Anthropic)** — apoio à redação dos cenários no formato do enunciado e da
  tabela de rastreabilidade.

## Resiliência e arquitetura do T2

> Inclui também a escala e a pontuação de risco de `docs/riscos.md`.

- Reutiliza a referência **3** (OWASP OAT): **OAT-021 Denial of Inventory** caracteriza a
  ameaça prioritária e sustenta a nota de probabilidade 3.
- Reutiliza a referência **4** (Anderson): a assimetria de custos entre atacante e defensor
  sustenta o critério de que um controle se justifica quando custa mais para A2 do que
  para A1.

### Ferramentas utilizadas nesta seção

- **Mermaid (mermaid-cli)** — diagrama de arquitetura do Trabalho 2. Fonte editável em
  `diagramas/arquitetura-t2.mmd`, exportado para `diagramas/arquitetura-t2.svg` e `.png`.

### Ferramentas de IA generativa utilizadas nesta seção

- **Claude (Anthropic)** — apoio à redação e estruturação da escala de risco, da resposta à
  ameaça prioritária e do diagrama de arquitetura.
