# Referências

> Arquivo colaborativo. As fontes de cada seção entram sob o cabeçalho correspondente,
> mantendo a numeração contínua e o padrão de formatação abaixo.
> A conferência final e a padronização são tarefa coletiva antes da entrega.

**Padrão adotado:** AUTOR/INSTITUIÇÃO. *Título*. Edição/Publicação, ano. Disponível em:
`<url>`. Acesso em: dd/mm/aaaa.

---

## Seção 3.1 — Descrição do sistema adversarial

1. **ESTADOS UNIDOS.** *Better Online Ticket Sales Act of 2016 (BOTS Act)*. Public Law
   114-274, 14 dez. 2016. Disponível em:
   `https://www.congress.gov/bill/114th-congress/senate-bill/3183`. Fonte primária que caracteriza legalmente a burla de medidas de controle de
   aquisição em plataformas de venda de ingressos. Sustenta o pressuposto **P1**
   (uma identidade corresponde a uma pessoa) e a caracterização do ator **A2**.

2. **FEDERAL TRADE COMMISSION (FTC).** *Online Event Ticket Sales: Enforcement of the
   BOTS Act*, sendo materiais públicos de fiscalização e orientação ao consumidor.
   Disponível em: `https://www.ftc.gov/`. Sustenta a caracterização do mercado secundário como fonte do incentivo econômico
   de **A2**.

3. **OWASP FOUNDATION.** *OWASP Automated Threats to Web Applications* (catálogo OAT).
   Disponível em: `https://owasp.org/www-project-automated-threats-to-web-applications/`. Categorias utilizadas: **OAT-021 Denial of Inventory** (base do pressuposto **P2**),
   **OAT-019 Account Creation** (base de **P1**) e **OAT-006 Expediting** (base de **P5**).
4. **ANDERSON, Ross.** *Security Engineering: A Guide to Building Dependable Distributed
   Systems*. 3. ed. Indianapolis: Wiley, 2020.
   — Economia da segurança e assimetria de custos entre atacante e defensor; sustenta a
   seção 7 (restrições e custos) e o pressuposto **P5**.

### Ferramentas utilizadas nesta seção

- **FigJam (Figma)** — produção dos diagramas de contexto. Exportado para
  `diagramas/contexto.svg` (Fig. 1, DFD nível 0),
  `diagramas/contexto-fluxo.svg` (Fig. 2) e `diagramas/contexto-legenda.svg`.

### Ferramentas de IA generativa utilizadas nesta seção

- **ChatGPT (OpenAI)** — *brainstorming* da escolha do sistema e do recorte da interação.
- **Claude (Anthropic)** — apoio à redação e estruturação da seção 3.1.

> Todo conteúdo gerado foi revisado manualmente quanto à aderência ao enunciado, à
> consistência interna do recorte e à existência e correção das fontes citadas.

---

## Seção 3.2 — Modelo estratégico estático

> *Pendente.*

## Seção 3.3 — Modelo estratégico dinâmico

- Reutiliza a referência **3** (OWASP OAT): **OAT-021 Denial of Inventory** sustenta a
  imobilização de estoque da rodada 3.

### Ferramentas utilizadas nesta seção

- **Mermaid (mermaid-cli)** — diagrama do ciclo adaptativo. Fonte editável em
  `diagramas/ciclo-adaptativo.mmd`, exportado para `diagramas/ciclo-adaptativo.svg` e `.png`.

### Ferramentas de IA generativa utilizadas nesta seção

- **Claude (Anthropic)** — apoio à redação e estruturação da seção 3.3.

## Seção 3.4 — Superfície de ataque

- Reutiliza a referência **3** (OWASP OAT): **OAT-021 Denial of Inventory** sustenta PE2 e PE3, **OAT-019 Account Creation** sustenta PE4 e PE8, e **OAT-006 Expediting** sustenta PE1.

5. **OWASP FOUNDATION.** *Attack Surface Analysis Cheat Sheet*. OWASP Cheat Sheet Series. Disponível em: `https://cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html`. Base do método usado: enumerar pontos de entrada e saída, separar o que é controlado pelo cliente e rever a superfície a cada mudança no sistema.

6. **MITRE.** *CWE-367: Time-of-check Time-of-use (TOCTOU) Race Condition*. Common Weakness Enumeration. Disponível em: `https://cwe.mitre.org/data/definitions/367.html`. Caracteriza a fraqueza de implementação de PE5 (verificar o limite e gravar a reserva sem atomicidade).

### Ferramentas utilizadas nesta seção

- **Mermaid (mermaid-cli)**: diagrama de superfície de ataque. Fonte editável em `diagramas/superficie-de-ataque.mmd`, exportado para `diagramas/superficie-de-ataque.svg` e `.png`.

### Ferramentas de IA generativa utilizadas nesta seção

- **Claude (Anthropic)**: apoio à redação e estruturação dos pontos de exploração, das tabelas de rastreabilidade e do diagrama de superfície de ataque.

## Seção 3.4 — Cenários de ameaça

- Reutiliza a referência **3** (OWASP OAT): **OAT-021 Denial of Inventory** caracteriza T1 e
  **OAT-019 Account Creation**, T2.
- Reutiliza a referência **6** (MITRE CWE-367): caracteriza a parte de T2 que explora a
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
