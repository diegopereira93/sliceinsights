# Phase 17: UI Redesign com Stitch — Research

**Pesquisado em:** 2026-03-23
**Domínio:** UI Implementation — Google Stitch AI, Next.js 14, Tailwind CSS, Framer Motion
**Confiança geral:** MEDIUM (designs Stitch não puderam ser acessados diretamente — projeto privado requer autenticação interativa; pesquisa cobre workflow, stack e padrões com HIGH confidence)

---

## Research Summary

### Contexto da fase

A Phase 17 implementa os designs gerados pelo Google Stitch AI para quatro telas do SliceInsights: **Elite Racket Catalog** (home `/`), **Premium Home** (hero section), **Quiz Técnico** (`/recommend`), e **Analytics** (`/statistics`). O objetivo é elevar a qualidade visual da UI de "funcional" para "premium" — mantendo o design system existente (preto #000000, verde-limão `#ceff00`, glassmorphism, tipografia italic/bold uppercase).

### Estado atual da UI

A UI atual é funcional mas inconsistente:
- **Home (`/`)**: Bem estruturada — hero animado, toolbar sticky, grid de cards com glassmorphism, "Modo de Batalha", quiz modal. Design coeso e premium.
- **Quiz/Recommend (`/recommend`)**: Significativamente mais simples — usa classes hardcoded (`bg-[#111111]`, `border-[#222222]`) sem o design system compartilhado. Sem framer-motion, sem componentes de UI reutilizáveis. Discrepância visual óbvia com a home.
- **Statistics (`/statistics`)**: Usa o design system via `statistics-client.tsx` com Recharts, componentes de UI, e Framer Motion — estado mais próximo do nível premium.

### Stitch MCP — status de acesso

O projeto Stitch (ID `1614867386643086273`) retornou 404 via browser headless mesmo com perfis Chrome autenticados. O Stitch usa autenticação Google OAuth que não persiste em sessões headless. **Bloqueio de acesso aos designs** — ver seção Risks & Blockers.

O Stitch MCP (`@_davideast/stitch-mcp`) **existe oficialmente** e é o canal correto para integrar designs no workflow de código. Deve ser configurado antes do planejamento de tasks.

**Recomendação principal:** Configurar o Stitch MCP com API key antes de começar a implementação, e usar `get_screen_code` + `get_screen_image` para extrair HTML/Tailwind de cada screen. A implementação em Next.js adapta esse código ao design system existente — não substitui componentes funcionais.

---

## Technology Stack & Patterns

### Stack atual (confirmado via codebase)

| Tecnologia | Versão | Papel |
|------------|--------|-------|
| Next.js | 14.2.35 | Framework (App Router, SSR/ISR) |
| React | 18.3.1 | UI runtime |
| TypeScript | 5.9.3 | Tipagem |
| Tailwind CSS | 3.4.19 | Utility-first styling |
| Framer Motion | 11.11.17 | Animações e transições |
| Radix UI | vários | Componentes primitivos acessíveis |
| Lucide React | 0.562.0 | Ícones |
| Recharts | 3.6.0 | Gráficos (Statistics) |
| Vaul | 1.1.2 | Drawer nativo mobile |
| class-variance-authority | 0.7.1 | Variantes de componentes |
| clsx + tailwind-merge | - | Merging de classes |

### Design System existente (tailwind.config.js)

```javascript
colors: {
  primary: { DEFAULT: '#ceff00', foreground: '#000000' },
  background: '#000000',
  foreground: '#ffffff',
  muted: { DEFAULT: '#111111', foreground: '#a1a1aa' },
  border: '#222222',
  'primary-text': '#ceff00',
}
// Utilitários CSS: .glass, .glass-card, .text-glow, .glow-hover
// Tipografia: font-black italic uppercase tracking-tighter (padrão hero)
// Border radius: sm=0.5, md=0.75, lg=1, xl=1.5, 2xl=2, 3xl=2.5rem
// Shadows: glass, glow (primary/30)
```

### Stitch MCP — ferramentas disponíveis

| Tool | Função | Uso na fase |
|------|---------|-------------|
| `get_screen_code` | Baixa HTML/Tailwind de uma screen | Extrair código de cada design |
| `get_screen_image` | Baixa screenshot base64 de uma screen | Referência visual para implementação |
| `build_site` | Mapeia screens para rotas, retorna HTML de cada página | Exportar projeto completo de uma vez |

**Configuração do MCP:**
```json
{
  "mcpServers": {
    "stitch": {
      "command": "npx",
      "args": ["@_davideast/stitch-mcp", "proxy"]
    }
  }
}
```

Requer `STITCH_API_KEY` (obtida em Stitch → Profile → Settings → API Key) ou OAuth via `npx @_davideast/stitch-mcp init`.

### Workflow de implementação Stitch → Next.js

```
Stitch Project (designs)
    ↓ [get_screen_code via MCP]
HTML + Tailwind CSS (export raw)
    ↓ [análise + decomposição]
Mapeamento de componentes existentes vs novos
    ↓ [implementação]
React/TSX com design system do projeto
    + framer-motion para animações
    + Radix UI para interatividade
    + tokens do tailwind.config.js (não inline)
    ↓ [responsividade]
Mobile-first (app é PWA mobile-first com BottomNav)
    + breakpoints: sm(640), md(768), lg(1024), xl(1280)
    ↓ [validação]
Playwright E2E + inspeção visual
```

### Padrão de componente no projeto

Componentes seguem o padrão `'use client'` com imports centralizados:
- UI primitivos: `@/components/ui/`
- Domínio: `@/components/paddle/`, `@/components/statistics/`
- Páginas: SSR em `app/*/page.tsx`, lógica cliente em `*-client.tsx`
- Classes Tailwind via tokens — evitar hardcode de cores hex

---

## Architecture Patterns

### Estrutura atual do frontend

```
frontend/
├── app/
│   ├── layout.tsx          # MobileLayout wrapper, Inter font, dark class
│   ├── page.tsx            # Home SSR → HomeClient
│   ├── recommend/page.tsx  # Quiz/Recommend (cliente puro — precisa redesign)
│   ├── statistics/page.tsx # SSR → StatisticsClient
│   └── globals.css         # .glass, .glass-card, scrollbar, safe-areas
├── components/
│   ├── ui/                 # Primitivos (button, card, badge, drawer, etc.)
│   ├── paddle/             # PaddleCard, FilterDrawer, QuizModal, Comparator
│   ├── statistics/         # Recharts wrappers, LeaderboardCard, etc.
│   ├── layout/mobile-layout.tsx
│   └── home-client.tsx
└── tailwind.config.js      # Design tokens centralizados
```

### Padrão de redesign por tela

Para cada tela identificada no Stitch, o padrão é:

**1. Elite Racket Catalog (Home `/`)** — Estado atual: BOM
- Foco: refinar visual dos PaddleCards, melhorar hero section
- Preservar: lógica de filtros, comparador, quiz modal
- Risco: regressão funcional ao redesenhar

**2. Premium Home (Hero Section)** — Estado atual: BOM
- Foco: elevar o hero com elementos do design Stitch (pode incluir paddle 3D, stats animadas)
- Preservar: botões CTA, animações Framer Motion existentes

**3. Quiz Técnico (`/recommend`)** — Estado atual: RUIM (discrepância visual severa)
- Prioridade máxima de redesign
- Usar componentes `@/components/ui/` em vez de classes hardcoded
- Adicionar framer-motion para transições entre steps
- Alinhar ao design system (tokens, não `bg-[#111111]`)

**4. Analytics (`/statistics`)** — Estado atual: MÉDIO
- Foco: melhorar layout geral, tabs, apresentação de dados
- Preservar: lógica Recharts complexa e filtros de ScatterChart

### Anti-padrões a evitar

- **Não usar cores hex inline** — usar tokens do tailwind.config.js (`bg-muted`, `text-primary`, etc.)
- **Não quebrar componentes funcionais** — redesign de estilo, não de lógica
- **Não remover framer-motion onde existe** — adicionar onde falta, não remover
- **Não substituir Radix UI por HTML nativo** — manter acessibilidade
- **Não ignorar mobile-first** — o app é PWA; verificar em 375px primeiro

---

## Validation Architecture

### Framework de testes existente

| Propriedade | Valor |
|-------------|-------|
| Framework | Playwright (`@playwright/test` 1.58.2) |
| Config | `frontend/` (playwright via npm scripts) |
| Comando rápido | `cd frontend && BASE_URL=http://localhost:3002 API_URL=http://localhost:8002/api/v1 npx playwright test --reporter=list` |
| Suite completa | `npm run test:e2e:local` |
| E2E files existentes | `e2e/sliceinsights.spec.ts`, `recommendation-e2e.spec.ts`, `catalog-ingestion.spec.ts` |

### Mapa de requisitos → testes para Phase 17

| Requisito | Comportamento | Tipo de Teste | Status |
|-----------|--------------|---------------|--------|
| UI-01: Home premium | Cards com design Stitch, hero elevado | Visual/E2E smoke | Novo |
| UI-02: Quiz redesenhado | Steps com design system, framer-motion | E2E funcional | Atualizar spec existente |
| UI-03: Analytics redesenhado | Tabs e charts com layout correto | E2E smoke | Novo |
| UI-04: Responsividade | Todas as telas ok em 375px, 768px, 1280px | Playwright resize | Novo |
| UI-05: Regressão funcional | Filtros, comparador, quiz, chat funcionam | E2E funcional | Preservar specs existentes |

### Wave 0 — gaps antes da implementação

- [ ] `frontend/e2e/ui-redesign-smoke.spec.ts` — visual smoke para Home, Quiz, Statistics
- [ ] `frontend/e2e/responsiveness.spec.ts` — viewport 375, 768, 1280 para cada rota
- [ ] Verificar que specs existentes (`recommendation-e2e.spec.ts`) passam no estado atual antes de qualquer mudança

### Gate da fase

Todos os testes E2E existentes devem continuar passando + novos smoke tests devem passar antes de `/gsd:verify-work`.

---

## Risks & Blockers

### Bloqueador crítico: Acesso aos designs Stitch

**Problema:** O projeto Stitch (ID `1614867386643086273`) retorna 404 em browser headless. O Stitch requer autenticação Google OAuth interativa — o browser headless não consegue usar as sessões do Chrome instalado por restrições do Google OAuth.

**Impacto:** A fase não pode extrair o código/screenshots dos designs sem acesso.

**Resolução necessária (Wave 0 obrigatória):**
1. O usuário precisa gerar uma **API key do Stitch** (Stitch → Profile → Settings → API Key)
2. Configurar `STITCH_API_KEY` no ambiente ou via `npx @_davideast/stitch-mcp init`
3. Adicionar configuração do MCP stitch ao `.claude/settings.json` do projeto
4. Validar acesso com `npx @_davideast/stitch-mcp serve -p 1614867386643086273`

**Alternativa se Stitch MCP não funcionar:** O usuário exporta manualmente cada screen como HTML ou screenshot do Stitch e coloca em `.planning/phases/17-*/designs/`. A implementação usa essas referências visuais.

**Confiança no design Stitch:** LOW — designs não puderam ser inspecionados. O planner deve estruturar Wave 0 para incluir a extração de designs como pré-requisito bloqueante.

### Risco 2: Discrepância visual entre telas

**Problema:** A page `/recommend` usa classes hardcoded (`bg-[#111111]`) enquanto o resto usa tokens. Redesenhar sem remover a lógica de state machine (step 0→1→2→'result') é delicado.

**Como evitar:** Separar redesign de estilo da lógica de negócio. Criar `RecommendClient` com o mesmo state mas novos componentes visuais.

### Risco 3: Regressão nos testes E2E existentes (26/26 passando na Phase 15.4)

**Problema:** Qualquer mudança nos seletores, classes, ou estrutura HTML pode quebrar os 26 testes Playwright existentes.

**Como evitar:** Executar `npm run test:e2e:local` antes e depois de cada wave. Adicionar `data-testid` attrs onde faltam — não depender de classes CSS como seletores.

### Risco 4: Responsividade mobile quebrada

**Problema:** O app é PWA mobile-first com `MobileLayout` e `BottomNav`. Qualquer redesign que ignore o contexto mobile (375px viewport, safe-area-inset) vai quebrar a experiência principal.

**Como evitar:** Testar em viewport 375px como primeiro breakpoint. O Stitch geralmente gera para mobile mas pode ter gaps de responsividade.

### Risco 5: Stitch gera HTML com classes conflitantes

**Problema:** O Stitch pode exportar Tailwind com versões de classe diferentes da v3.4 usada no projeto, ou com prefixos que conflitam.

**Como evitar:** Nunca copiar o HTML do Stitch diretamente — sempre adaptar ao design system do projeto via tokens existentes.

---

## Phase Boundary & Scope

### O que ENTRA nesta fase

- Redesign visual das 4 telas: Home (catalog + hero), Quiz Técnico (`/recommend`), Analytics (`/statistics`)
- Alinhamento do `/recommend` ao design system (substituir classes hardcoded por tokens)
- Adição de framer-motion ao `/recommend` (atualmente sem animações)
- Responsividade verificada em 375px, 768px, 1280px para todas as telas
- Novos smoke tests E2E para as 4 telas
- Configuração do Stitch MCP como pré-requisito

### O que NÃO entra nesta fase

- Novos endpoints de backend
- Novos campos/specs no banco de dados
- Mudanças na lógica de filtragem, comparação ou recomendação
- Substituição de bibliotecas (Recharts, Radix UI, Framer Motion)
- Novo design system (tokens do tailwind.config.js são mantidos)
- Novas páginas ou rotas
- Funcionalidades de dados (scraping, ingestion)

### Dependências confirmadas

- Phase 16 completa: dados limpos (sem Unsplash, brands corretas) — ✅ completa em 2026-03-23
- Stitch MCP configurado com API key — BLOQUEANTE (Wave 0)
- App rodando localmente com Docker (`docker-compose up`) para testes E2E

---

## Recommendations

### Para o planner

**Estruture a fase em 3 waves:**

**Wave 0 — Setup e extração de designs (BLOQUEANTE)**
- Configurar Stitch MCP (`STITCH_API_KEY`)
- Extrair code + screenshots de cada screen via `get_screen_code`
- Inventariar o que existe no Stitch vs o que precisa ser criado
- Executar suite E2E existente e documentar baseline (26/26 passando)

**Wave 1 — Quiz Técnico (`/recommend`) — maior impacto**
- É a tela mais desalinhada com o design system
- Criar componentes novos ou reusar `@/components/ui/` existentes
- Adicionar framer-motion para step transitions
- Substituir todas as classes hardcoded por tokens

**Wave 2 — Home e Analytics**
- Home: refinar PaddleCard e hero (já está bem)
- Analytics: ajustar layout e apresentação de tabs
- Menor risco de regressão que o Quiz

**Wave 3 — Responsividade e validação**
- Viewport tests (375, 768, 1280)
- Suite E2E completa
- Human checkpoint visual

**Priorização se tempo for limitado:** Quiz Técnico > Analytics > Home (a home já está premium).

### Decisões para o usuário definir antes do planejamento

1. **API key do Stitch disponível?** Se sim, configurar antes. Se não, o planner deve incluir passo manual.
2. **Os designs Stitch estão completos para as 4 telas?** Ou precisam ser gerados ainda?
3. **Preservar a estrutura atual do `/recommend` (wizard 3 steps) ou redesenhar o fluxo?** A pesquisa sugere preservar o fluxo, redesenhar apenas o visual.
4. **Nível de fidelidade ao Stitch:** Pixel-perfect (alto esforço) vs. inspiração visual (médio esforço)?

### Padrões confirmados para usar

**Não reinventar:**
- Glassmorphism via `.glass-card` (já em `globals.css`)
- Animações de entrada: `initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}`
- Cards: `<Card className="glass-card border-none overflow-hidden group hover:ring-2 hover:ring-primary/30">`
- Botão primário: `bg-primary text-primary-foreground font-black rounded-2xl`
- Badges: `bg-white/10 backdrop-blur-md border border-white/20 font-black italic uppercase`

**Padrão de componente Quiz alinhado ao design system:**
```tsx
// ANTES (hardcoded — evitar)
<button className="border-[#ceff00] bg-[#ceff00]/10 text-[#ceff00]">

// DEPOIS (tokens — usar)
<Button variant="outline" className="border-primary bg-primary/10 text-primary font-black rounded-full">
```

---

## Sources

### Primárias (HIGH confidence — codebase direto)
- `/frontend/tailwind.config.js` — Design tokens completos
- `/frontend/app/globals.css` — Utilitários CSS (.glass, .glass-card)
- `/frontend/app/layout.tsx` — Fontes, MobileLayout, dark class
- `/frontend/components/home-client.tsx` — Padrão de referência da UI premium
- `/frontend/app/recommend/page.tsx` — Estado atual do Quiz (discrepância identificada)
- `/frontend/package.json` — Stack e versões confirmadas

### Secundárias (MEDIUM confidence — múltiplas fontes concordantes)
- [Google Stitch Blog (Google Developers)](https://developers.googleblog.com/stitch-a-new-way-to-design-uis/) — Lançamento e export capabilities
- [stitch-mcp GitHub (davideast)](https://github.com/davideast/stitch-mcp) — Tools: `get_screen_code`, `build_site`, `get_screen_image`
- [Stitch MCP npm](https://www.npmjs.com/package/@_davideast/stitch-mcp) — Configuração do MCP server
- [Google Codelabs: Design-to-Code com Stitch MCP](https://codelabs.developers.google.com/design-to-code-with-antigravity-stitch?hl=en) — Workflow oficial
- [LogRocket: Vibe-based UI com Stitch](https://blog.logrocket.com/google-stitch-tutorial/) — Pitfalls de responsividade e integração

### Terciárias (LOW confidence — verificação pendente)
- Detalhes exatos dos designs Stitch para este projeto — não acessados (bloqueio de autenticação)
- Versão atual do Stitch MCP e compatibilidade com STITCH_API_KEY — requer teste real

---

## Metadata

**Breakdown de confiança:**
- Stack e design system atual: HIGH — verificado diretamente no codebase
- Stitch workflow e MCP tools: MEDIUM — múltiplas fontes concordantes, não testado no projeto
- Conteúdo dos designs Stitch: LOW — projeto inacessível via headless; requer configuração manual de API key
- Pitfalls de implementação: MEDIUM — fontes externas verificadas, razoavelmente consensuais

**Data da pesquisa:** 2026-03-23
**Válido até:** 2026-04-23 (Stitch é produto em evolução rápida — verificar changelog)
