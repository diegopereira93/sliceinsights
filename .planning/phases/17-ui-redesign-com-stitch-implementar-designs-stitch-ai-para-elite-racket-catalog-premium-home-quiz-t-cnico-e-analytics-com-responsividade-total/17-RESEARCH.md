# Phase 17: UI Redesign com Stitch — Research

**Pesquisado em:** 2026-03-23 (atualizado — investigação completa do codebase)
**Domínio:** UI Implementation — Google Stitch AI MCP, Next.js 14, Tailwind CSS, Framer Motion
**Confiança geral:** MEDIUM-HIGH (stack atual: HIGH — codebase verificado diretamente; workflow Stitch: MEDIUM — MCP não testado no projeto; designs Stitch: LOW — requer configuração de API key)

---

## Summary

A Phase 17 implementa designs gerados pelo Google Stitch AI para quatro telas do SliceInsights: **Elite Racket Catalog** (home `/`), **Premium Home** (hero section), **Quiz Técnico** (`/recommend`), e **Analytics** (`/statistics`). O stack é Next.js 14 + Tailwind CSS 3.4 + Framer Motion 11 — nenhuma nova biblioteca é necessária.

O maior problema identificado é o `/recommend/page.tsx`: **todo o arquivo usa classes hardcoded** (`bg-[#111111]`, `border-[#ceff00]`, `bg-[#000000]`) em vez dos tokens do design system. Isso cria discrepância visual severa com as outras páginas. O redesign do Quiz Técnico é a tarefa de maior valor e risco desta fase.

O MCP do Stitch (`@_davideast/stitch-mcp`) não está configurado no projeto (`.claude/settings.json` não tem `mcpServers`). A Wave 0 deve incluir setup obrigatório do MCP antes de qualquer implementação.

**Recomendação principal:** Wave 0 configura Stitch MCP + extrai designs. Wave 1 redesenha `/recommend` (maior impacto). Wave 2 refina Home e Statistics. Wave 3 valida responsividade e roda suite E2E completa.

---

## Standard Stack

### Core (confirmado via codebase — HIGH confidence)

| Biblioteca | Versão | Papel | Notas |
|------------|--------|-------|-------|
| Next.js | 14.2.35 | Framework (App Router, SSR/ISR) | Estrutura de rotas imutável |
| React | 18.3.1 | UI runtime | `'use client'` em páginas com estado |
| TypeScript | 5.9.3 | Tipagem | Todos os componentes em `.tsx` |
| Tailwind CSS | 3.4.19 | Utility-first styling | Tokens em `tailwind.config.js` — usar sempre |
| Framer Motion | 11.11.17 | Animações e transições | Presente em Home e Statistics — ausente no Quiz |
| Radix UI | vários | Componentes primitivos acessíveis | Drawer, Dialog, Tabs, Select, Tooltip |
| Lucide React | 0.562.0 | Ícones | Padrão em todo o projeto |
| Recharts | 3.6.0 | Gráficos | Usado em Statistics — não substituir |
| Vaul | 1.1.2 | Drawer nativo mobile | Usado em FilterDrawer |
| class-variance-authority | 0.7.1 | Variantes de componentes | Pattern `cva()` nos componentes UI |
| clsx + tailwind-merge | - | Merging de classes | Padrão `cn()` em `lib/utils.ts` |

### Stitch MCP (não instalado — setup Wave 0)

| Pacote | Comando de instalação | Configuração |
|--------|-----------------------|--------------|
| `@_davideast/stitch-mcp` | `npx @_davideast/stitch-mcp init` | `.claude/settings.json` → `mcpServers.stitch` |

**Status atual:** `.claude/settings.json` tem `mcpServers: []` — MCP não configurado.

**Ferramentas do MCP disponíveis após setup:**

| Tool | Função | Uso na fase |
|------|---------|-------------|
| `create_project` | Cria novo projeto Stitch | Caso designs não existam |
| `generate_screen_from_text` | Gera screen a partir de prompt de texto | Gerar telas com prompt descritivo |
| `generate_variants` | Gera variantes de uma screen | Explorar opções de design |
| `get_project` | Lê metadados do projeto | Verificar projeto existente |
| `list_projects` | Lista projetos disponíveis | Descobrir projetos do usuário |
| `list_screens` | Lista screens de um projeto | Inventariar designs existentes |
| `get_screen` | Lê uma screen específica | Extrair código/screenshot de cada tela |
| `edit_screens` | Edita screens existentes | Refinar designs gerados |

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

Requer `STITCH_API_KEY` obtida em Stitch → Profile → Settings → API Key, ou OAuth via `npx @_davideast/stitch-mcp init`.

---

## Architecture Patterns

### Estrutura atual do frontend (verificada no codebase)

```
frontend/
├── app/
│   ├── layout.tsx           # MobileLayout wrapper, Inter font, dark class
│   ├── page.tsx             # Home SSR — chama HomeClient
│   ├── globals.css          # .glass, .glass-card, scrollbar, safe-areas
│   ├── recommend/
│   │   └── page.tsx         # Quiz/Recommend — 'use client', SEM SSR, SEM framer-motion
│   ├── statistics/
│   │   └── page.tsx         # SSR — chama StatisticsClient
│   └── [outras rotas]
├── components/
│   ├── ui/                  # Primitivos (button, card, badge, drawer, tabs, etc.)
│   │   └── [24 componentes]
│   ├── paddle/              # PaddleCard, FilterDrawer, QuizModal, Comparator, DetailDrawer
│   ├── statistics/          # Recharts wrappers, LeaderboardCard, DistributionChart, etc.
│   ├── layout/mobile-layout.tsx
│   ├── home-client.tsx      # Referência premium: framer-motion + Radix + design tokens
│   └── statistics-client.tsx  # Usa design tokens corretamente
└── e2e/
    ├── sliceinsights.spec.ts         # 218 linhas — Home, filtros, quiz
    ├── recommendation-e2e.spec.ts    # 110 linhas — fluxo de recomendação
    ├── catalog-ingestion.spec.ts     # 53 linhas — ingestion validation
    └── battle-bar.spec.ts            # 23 linhas — battle bar
```

### Diagnóstico por tela

**1. Home `/` — Estado: BOM (referência premium)**
- `page.tsx` → SSR → `HomeClient` (`'use client'`)
- Usa: framer-motion (`motion`, `AnimatePresence`), Radix UI, todos os tokens do design system
- Componentes: `PaddleCard`, `FilterDrawer`, `RacketFinderQuiz`, `PaddleDetailDrawer`, `PaddleComparator`
- Foco do redesign: refinar `PaddleCard` visual e hero section conforme Stitch
- Risco: MÉDIO — lógica complexa de filtros e comparador; redesign só no visual

**2. Quiz Técnico `/recommend` — Estado: RUIM (discrepância severa)**
- `page.tsx` inteiro é `'use client'` — sem SSR, sem Server Component wrapper
- **100% classes hardcoded** — exemplos reais do código:
  - `bg-[#000000]`, `bg-[#111111]`, `border-[#222222]`, `border-[#ceff00]`
  - `bg-[#ceff00]/10`, `text-[#ceff00]`, `bg-[#ceff00]`, `text-black`
  - `bg-[#1a1a1a]`, `bg-[#0a0a0a]`, `border-2 border-[#ceff00]`
- Sem framer-motion (nenhum import de `motion`)
- Usa `<button>` HTML nativo em vez de `<Button>` do Radix
- Usa `<input>` HTML nativo em vez de `<Input>` do design system
- State machine: Step 0 (skill+style) → Step 1 (budget) → Step 2 (health+weight) → 'result'
- **Preservar toda a lógica de state** — só redesenhar a camada visual
- Risco: ALTO — maior trabalho, lógica complexa de chat e API calls

**3. Analytics `/statistics` — Estado: MÉDIO (usa tokens, mas layout pode melhorar)**
- `page.tsx` → SSR → `StatisticsClient` (`'use client'`)
- `StatisticsClient` usa tokens corretamente: `bg-background`, `border-border`, `text-muted-foreground`
- Usa framer-motion, Recharts, Radix Tabs, Drawer, Badge
- Foco do redesign: layout geral, tabs, apresentação de dados conforme Stitch
- Risco: MÉDIO — Recharts é sensível a mudanças de layout

**4. Premium Home (hero section) — Estado: BOM (já premium)**
- Mesma página que Home `/` — hero está em `HomeClient`
- Componente hero usa `motion.div` + gradientes + tipografia `font-black italic uppercase tracking-tighter`
- Foco: elevar hero conforme design Stitch (pode incluir stats animadas)
- Risco: BAIXO — mudanças cosméticas no hero section

### Workflow Stitch → Next.js

```
1. Wave 0: Configurar Stitch MCP
   ├── npx @_davideast/stitch-mcp init (OAuth ou STITCH_API_KEY)
   ├── Adicionar mcpServers.stitch ao .claude/settings.json
   └── list_projects → descobrir projeto existente OU create_project

2. Wave 0: Extrair designs
   ├── list_screens → inventariar screens disponíveis
   ├── get_screen → HTML/CSS + screenshot de cada tela
   └── Salvar referências em .planning/phases/17-*/designs/

3. Wave 0: Baseline E2E
   └── npm run test:e2e:local → documentar estado (deve estar 26/26 passing)

4. Por tela: Adaptar design Stitch ao projeto
   ├── Analisar HTML/Tailwind exportado pelo Stitch
   ├── Mapear para tokens existentes (NÃO copiar classes literalmente)
   ├── Substituir elementos HTML nativos por componentes @/components/ui/
   ├── Adicionar framer-motion onde ausente
   └── Mobile-first: testar 375px primeiro

5. Wave 3: Validação
   ├── Playwright viewport tests: 375, 768, 1280
   └── npm run test:e2e:local → todos devem passar
```

### Padrão de componente: de hardcoded para design system

```tsx
// ANTES — padrão atual do /recommend (evitar)
<button className={`px-4 py-2 rounded-full border transition-colors ${
  selected ? 'border-[#ceff00] bg-[#ceff00]/10 text-[#ceff00]' : 'border-[#222222] text-gray-300'
}`}>

// DEPOIS — padrão do design system (usar)
<Button
  variant={selected ? "default" : "outline"}
  className={cn(
    "rounded-full font-black",
    selected && "ring-2 ring-primary"
  )}
>
```

```tsx
// ANTES — input hardcoded
<input className="bg-[#111111] border border-[#222222] rounded-lg px-4 py-3 text-white focus:border-[#ceff00]" />

// DEPOIS — Input do design system
<Input className="bg-muted border-border focus:ring-primary rounded-xl" />
```

### Padrões confirmados do design system (NÃO reinventar)

```tsx
// Glassmorphism card
<Card className="glass-card border-none overflow-hidden group hover:ring-2 hover:ring-primary/30">

// Botão primário
<Button className="bg-primary text-primary-foreground font-black rounded-2xl">

// Badge premium
<Badge className="bg-white/10 backdrop-blur-md border border-white/20 font-black italic uppercase">

// Animação de entrada padrão
<motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>

// Título hero
<h1 className="font-black italic uppercase tracking-tighter text-4xl">
```

### Anti-padrões a evitar

- **Copiar classes Tailwind do Stitch literalmente** — Stitch pode usar versões/prefixos diferentes; sempre adaptar aos tokens do projeto
- **Usar cores hex inline** — usar `bg-primary`, `border-border`, `text-muted-foreground`, etc.
- **Substituir `<Button>` por `<button>`** — perder variantes, acessibilidade e estilo consistente
- **Ignorar mobile-first** — app é PWA; BottomNav ocupa `pb-20`; safe-area-inset deve ser respeitado
- **Quebrar data-testid seletores** — E2E usa seletores por role/text, mas mudanças estruturais podem quebrar 26 testes existentes
- **Remover framer-motion onde existe** — apenas adicionar onde falta, nunca remover

---

## Don't Hand-Roll

| Problema | Não construir | Usar | Por que |
|----------|---------------|------|---------|
| Seleção de opções no Quiz | `<button>` com classes manuais | `<Button variant="outline">` com `ring-primary` | Acessibilidade, estados :focus, :disabled |
| Input de orçamento | `<input>` hardcoded | `<Input>` do design system | Consistência visual, focus ring automático |
| Loading state | divs com `animate-pulse` hardcoded | `<Skeleton>` de `@/components/ui/skeleton` | Já existe no projeto |
| Chat messages | divs com bg hardcoded | Classes de tokens: `bg-muted`, `bg-primary/20` | Consistência com dark mode |
| Tabs em Analytics | HTML nativo | `<Tabs>` de `@/components/ui/tabs` (Radix) | Acessibilidade ARIA automática |
| Drawer/Sheet mobile | implementação custom | `<Drawer>` de Vaul ou `<Sheet>` de Radix | Animações nativas mobile já implementadas |
| Animações de step | CSS transitions manuais | `<AnimatePresence>` + `motion.div` do Framer | Sincronização de enter/exit já testada |

---

## Common Pitfalls

### Pitfall 1: Regressing E2E tests ao mudar estrutura HTML

**O que vai errado:** Alterar a estrutura semântica (remover `<main>`, mudar hierarquia de headings, remover botões) quebra os 26 testes Playwright existentes que usam seletores por role e texto.

**Por que acontece:** Os specs usam `page.locator('h1')`, `page.getByRole('navigation')`, `page.getByRole('button', { name: '...' })` — mudanças no DOM quebram esses seletores.

**Como evitar:** Executar `npm run test:e2e:local` antes e depois de cada wave. Manter `<main>`, `<h1>`, `<nav>` na mesma posição. Adicionar `data-testid` attrs onde seletores frágeis existirem.

**Sinais de alerta:** Testes falhando com `Locator.waitFor: Timeout` ou `Element not found`.

### Pitfall 2: Stitch exporta Tailwind com classes incompatíveis

**O que vai errado:** O Stitch usa Tailwind v4 ou variantes diferentes das do projeto (v3.4). Classes como `bg-zinc-950`, `text-lime-400`, `rounded-3xl` podem parecer equivalentes mas têm valores diferentes dos tokens do projeto.

**Por que acontece:** O Stitch tem seu próprio design system interno que não corresponde 1:1 ao design system do SliceInsights.

**Como evitar:** Nunca fazer copy-paste direto de classes do Stitch. Mapear explicitamente: `lime-400` → `primary (#ceff00)`, `zinc-950` → `background (#000000)`, `zinc-900` → `muted (#111111)`.

### Pitfall 3: Quiz perde state ao reestruturar componente

**O que vai errado:** A state machine do Quiz (`Step 0 → 1 → 2 → 'result'`) com `wizardState`, `result`, `messages`, `chatInput` é acoplada ao mesmo componente. Refatorar para sub-componentes sem cuidado pode causar re-renders que resetam o estado.

**Por que acontece:** Estado centralizado em `RecommendPage` — sub-componentes recebem callbacks. Se a estrutura de lifting state mudar, props podem ficar orphaned.

**Como evitar:** Manter toda a lógica de estado em `RecommendPage`. Criar sub-componentes visuais que recebem props e callbacks. Não criar contexto novo ou mover useState para sub-componentes.

### Pitfall 4: BottomNav obscurece conteúdo em mobile

**O que vai errado:** Conteúdo é adicionado no fundo da página mas fica escondido atrás do `BottomNav` em mobile (375px viewport).

**Por que acontece:** `MobileLayout` aplica `pb-20` ao container principal para dar espaço ao BottomNav fixo. Se um novo elemento tem `position: fixed` ou `padding-bottom` inadequado, o BottomNav sobrepõe.

**Como evitar:** Verificar sempre em viewport 375px. Usar `pb-20` ou `pb-safe` nos containers de página. Não usar `position: fixed` bottom sem considerar o BottomNav.

### Pitfall 5: Stitch MCP requer autenticação interativa

**O que vai errado:** `npx @_davideast/stitch-mcp` falha com erro de autenticação se não houver `STITCH_API_KEY` configurada.

**Por que acontece:** Stitch usa Google OAuth. Em ambientes headless, a autenticação OAuth não persiste.

**Como evitar:** Usar `STITCH_API_KEY` (token de API da conta Stitch) em vez de OAuth para acesso programático. Obter em Stitch → Profile → Settings → API Key.

---

## Code Examples

### Padrão SSR + Client Component (usar no Quiz se refatorar)

```tsx
// app/recommend/page.tsx — wrapper SSR (não existe hoje, pode ser criado)
import { RecommendClient } from '@/components/recommend/recommend-client';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Quiz Técnico | SliceInsights',
  description: 'Encontre sua raquete ideal com nosso assistente de IA',
};

export default function RecommendPage() {
  // Sem data fetching aqui — dados vêm via client fetch
  return <RecommendClient />;
}
```

### Padrão step-transition com Framer Motion (adicionar ao Quiz)

```tsx
// Source: padrão home-client.tsx do projeto
import { motion, AnimatePresence } from 'framer-motion';

// No render do Quiz:
<AnimatePresence mode="wait">
  {step === 0 && (
    <motion.div
      key="step-0"
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.2 }}
    >
      {/* Step 0 content */}
    </motion.div>
  )}
  {step === 1 && (
    <motion.div key="step-1" /* ... */>
      {/* Step 1 content */}
    </motion.div>
  )}
</AnimatePresence>
```

### Substituição de botão de seleção do Quiz

```tsx
// Source: padrão design system — tokens do tailwind.config.js
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// Botão de opção selecionável (skill level, play style, etc.)
<Button
  variant="outline"
  onClick={() => setWizardState(prev => ({ ...prev, skill_level: level }))}
  className={cn(
    "rounded-full font-black transition-all",
    wizardState.skill_level === level
      ? "border-primary bg-primary/10 text-primary ring-1 ring-primary"
      : "border-border text-muted-foreground hover:border-foreground/50"
  )}
>
  {label}
</Button>
```

### Viewport testing com Playwright (Wave 3)

```typescript
// Source: padrão Playwright — adicionar ao e2e/responsiveness.spec.ts
import { test, expect } from '@playwright/test';

const viewports = [
  { name: 'mobile', width: 375, height: 812 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 800 },
];

const routes = ['/', '/recommend', '/statistics'];

for (const viewport of viewports) {
  for (const route of routes) {
    test(`${route} renders correctly at ${viewport.name} (${viewport.width}px)`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto(route);
      await expect(page.locator('h1')).toBeVisible({ timeout: 10000 });
      // Verificar que nenhum elemento está fora da viewport
      const overflowX = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
      expect(overflowX).toBe(false);
    });
  }
}
```

---

## Validation Architecture

### Framework de testes existente

| Propriedade | Valor |
|-------------|-------|
| Framework | Playwright (`@playwright/test` — verificado em `e2e/` dir) |
| Specs existentes | `sliceinsights.spec.ts` (218 lin), `recommendation-e2e.spec.ts` (110 lin), `catalog-ingestion.spec.ts` (53 lin), `battle-bar.spec.ts` (23 lin) |
| Comando rápido | `cd frontend && BASE_URL=http://localhost:3002 API_URL=http://localhost:8002/api/v1 npx playwright test --reporter=list` |
| Suite completa | `npm run test:e2e:local` (em `frontend/`) |
| Baseline atual | 26/26 passando (confirmado Phase 15.4) |

### Mapa de requisitos → testes para Phase 17

| Req ID | Comportamento | Tipo de Teste | Comando Automatizado | Arquivo Existe? |
|--------|--------------|---------------|---------------------|----------------|
| UI-01 | Home/Catalog exibe cards com design Stitch premium | E2E smoke | `npx playwright test e2e/ui-redesign-smoke.spec.ts` | ❌ Wave 0 |
| UI-02 | Quiz Técnico usa design system (sem classes hardcoded) | E2E funcional | `npx playwright test e2e/recommendation-e2e.spec.ts` | ✅ (atualizar) |
| UI-03 | Analytics exibe tabs e gráficos com layout correto | E2E smoke | `npx playwright test e2e/ui-redesign-smoke.spec.ts` | ❌ Wave 0 |
| UI-04 | Todas as telas ok em 375px, 768px, 1280px | Playwright viewport | `npx playwright test e2e/responsiveness.spec.ts` | ❌ Wave 0 |
| UI-05 | Filtros, comparador, quiz, chat continuam funcionando | E2E regressão | `npm run test:e2e:local` | ✅ (preservar) |

### Sampling Rate

- **Por task commit:** `cd frontend && npx playwright test e2e/sliceinsights.spec.ts --reporter=list` (smoke da home)
- **Por wave merge:** `npm run test:e2e:local` (suite completa)
- **Phase gate:** Suite completa verde antes de `/gsd:verify-work`

### Wave 0 — gaps antes da implementação

- [ ] `frontend/e2e/ui-redesign-smoke.spec.ts` — smoke visual para Home, Quiz, Statistics (UI-01, UI-03)
- [ ] `frontend/e2e/responsiveness.spec.ts` — viewport 375, 768, 1280 para cada rota (UI-04)
- [ ] Baseline: executar `npm run test:e2e:local` e confirmar 26/26 antes de qualquer mudança
- [ ] Setup Stitch MCP: adicionar `mcpServers.stitch` ao `.claude/settings.json`
- [ ] Obter `STITCH_API_KEY` do Stitch → Profile → Settings → API Key

---

## Risks & Blockers

### Bloqueador crítico 1: Stitch MCP não configurado

**Problema:** `.claude/settings.json` não tem `mcpServers.stitch`. O `@_davideast/stitch-mcp` não está instalado localmente.

**Impacto:** Sem o MCP, as tools `list_projects`, `list_screens`, `get_screen`, `generate_screen_from_text` não estão disponíveis.

**Resolução (Wave 0 obrigatória):**
1. Obter `STITCH_API_KEY` em https://stitch.withgoogle.com → Profile → Settings → API Key
2. Adicionar ao `.claude/settings.json`:
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
3. Exportar `STITCH_API_KEY` no ambiente ou via `npx @_davideast/stitch-mcp init`
4. Validar com `mcp__stitch__list_projects`

**Alternativa se MCP não funcionar:** O usuário exporta cada screen como HTML/screenshot do Stitch e coloca em `.planning/phases/17-*/designs/`. A implementação usa essas referências visuais.

### Risco 2: Designs Stitch podem não existir ainda para este projeto

**Problema:** Não foi possível verificar se o projeto Stitch ID `1614867386643086273` tem as 4 screens completas, ou se elas precisam ser geradas.

**Impacto:** Se designs não existirem, Wave 0 inclui geração via `generate_screen_from_text` com prompts descritivos.

**Como mitigar:** Wave 0 executa `list_projects` → `list_screens` como primeiro passo. Se screens não existirem, usar `generate_screen_from_text` com prompts que descrevem o design system atual.

**Prompts de fallback para geração:**
- Home: `"Premium pickleball catalog page, dark theme (#000000 background, #ceff00 lime accent), glassmorphism cards, mobile-first, filtering sidebar"`
- Quiz: `"Multi-step recommendation wizard, 3 steps, dark theme, pill buttons for options, chat panel for AI results"`
- Statistics: `"Sports analytics dashboard, dark theme, scatter chart, tabs for overview/rankings/brands, badge-heavy data presentation"`

### Risco 3: Regressão nos 26 testes E2E existentes

**Problema:** Mudanças na estrutura HTML do `/recommend` (que tem 506 linhas, toda hardcoded) podem quebrar `recommendation-e2e.spec.ts`.

**Como mitigar:** Executar suite E2E antes e depois de cada wave. Verificar que seletores por role/text são preservados. Adicionar `data-testid` onde necessário.

### Risco 4: `/recommend` não tem Server Component wrapper

**Problema:** `app/recommend/page.tsx` é inteiramente `'use client'` (507 linhas). Sem Server Component wrapper, não há separação de preocupações e metadata SEO não é gerada.

**Oportunidade no redesign:** Criar `app/recommend/page.tsx` como Server Component (metadata, wrapper) e mover lógica para `components/recommend/recommend-client.tsx` — alinhando ao padrão da Home e Statistics.

**Risco:** Mudança estrutural maior. Se feita, requer validação E2E cuidadosa.

### Risco 5: Stitch gera classes Tailwind v4 incompatíveis com v3.4

**Problema:** O Stitch usa Tailwind v4 internamente. Classes como `bg-zinc-950`, `text-lime-400`, `inset-shadow-*` podem não existir no Tailwind v3.4 do projeto.

**Como mitigar:** Mapear explicitamente cores Stitch para tokens do projeto. Nunca copiar classes literalmente — sempre adaptar via `tailwind.config.js`.

---

## Phase Boundary & Scope

### O que ENTRA nesta fase

- Setup do Stitch MCP e extração dos designs (Wave 0)
- Redesign visual das 4 telas usando designs do Stitch como referência
- Migração do `/recommend` de classes hardcoded para tokens do design system
- Adição de framer-motion ao `/recommend` (step transitions + result animations)
- Criação de wrapper SSR para `/recommend` (alinhamento ao padrão do projeto) — se viável
- Responsividade verificada em 375px, 768px, 1280px para todas as telas
- Novos smoke tests E2E: `ui-redesign-smoke.spec.ts` + `responsiveness.spec.ts`

### O que NÃO entra nesta fase

- Novos endpoints de backend
- Novos campos/specs no banco de dados
- Mudanças na lógica de filtragem, comparação ou recomendação da IA
- Substituição de bibliotecas (Recharts, Radix UI, Framer Motion, Vaul)
- Novo design system (tokens do `tailwind.config.js` são mantidos)
- Novas páginas ou rotas
- Funcionalidades de dados (scraping, ingestion)

### Dependências confirmadas

- Phase 16 completa: dados limpos (sem Unsplash, brands corretas) — confirmado em STATE.md
- Stitch MCP configurado com API key — Wave 0 obrigatória
- App rodando localmente com Docker (`docker-compose up`) para testes E2E

---

## Recommendations para o Planner

### Estrutura de waves sugerida

**Wave 0 — Setup (bloqueante para tudo)**
1. Configurar Stitch MCP no `.claude/settings.json`
2. Obter e configurar `STITCH_API_KEY`
3. `list_projects` → `list_screens` → inventariar designs disponíveis
4. Se screens não existem: `generate_screen_from_text` para cada tela
5. `get_screen` para cada tela → salvar HTML/screenshot em `.planning/phases/17-*/designs/`
6. Executar `npm run test:e2e:local` → baseline 26/26
7. Criar `frontend/e2e/ui-redesign-smoke.spec.ts` e `responsiveness.spec.ts` (podem começar como mínimo viável)

**Wave 1 — Quiz Técnico `/recommend` (maior impacto, maior risco)**
1. Criar `app/recommend/page.tsx` como Server Component wrapper com metadata
2. Mover lógica para `components/recommend/recommend-client.tsx`
3. Substituir todos os `<button>` por `<Button>` do design system
4. Substituir todos os `<input>` por `<Input>` do design system
5. Migrar todas as classes hardcoded para tokens Tailwind
6. Adicionar `AnimatePresence` + `motion.div` para step transitions
7. Redesenhar cards de resultado e chat panel com design Stitch
8. Executar `npm run test:e2e:local` → deve manter 26/26

**Wave 2 — Home e Analytics (menor risco)**
1. Home: refinar `PaddleCard` visual conforme Stitch, elevar hero section
2. Analytics: ajustar layout tabs, melhorar apresentação de dados conforme Stitch
3. Executar `npm run test:e2e:local` após cada tela

**Wave 3 — Responsividade e validação final**
1. Completar `responsiveness.spec.ts` com todos os viewpoints
2. Viewport tests 375px, 768px, 1280px para todas as rotas
3. Suite E2E completa verde
4. Human checkpoint visual

### Priorização se tempo for limitado

**Quiz Técnico > Analytics > Home**

A home já está premium. O Quiz tem a maior discrepância visual e requer mais trabalho. Analytics tem estado médio e melhora incrementalmente.

### Decisão para o usuário confirmar antes do planejamento

1. **API key do Stitch disponível?** Configurar antes de Wave 0.
2. **Designs Stitch já existem para as 4 telas, ou precisam ser gerados?** Determina escopo de Wave 0.
3. **Criar wrapper SSR para `/recommend`?** Traz benefícios (metadata, padrão consistente) mas é mudança estrutural maior. Recomendação: sim, fazer nesta fase.
4. **Nível de fidelidade ao Stitch:** Pixel-perfect (alto esforço) vs. inspiração visual com design system existente (médio esforço). Recomendação: inspiração visual — usar Stitch como direção, não como spec rígida.

---

## Sources

### Primárias (HIGH confidence — codebase verificado diretamente)

- `/frontend/app/recommend/page.tsx` — Estado atual confirmado: 100% classes hardcoded, sem framer-motion
- `/frontend/components/home-client.tsx` — Padrão de referência premium: framer-motion, Radix, design tokens
- `/frontend/components/statistics-client.tsx` — Uso correto de tokens: `bg-background`, `border-border`
- `/frontend/tailwind.config.js` — Design tokens completos verificados
- `/frontend/app/globals.css` — Utilitários CSS (.glass, .glass-card, scrollbar, safe-areas)
- `/frontend/e2e/` — 4 specs E2E, 404 linhas total, baseline 26/26
- `/.claude/settings.json` — Confirmado: `mcpServers: []` — Stitch MCP não configurado
- `/.planning/config.json` — `nyquist_validation: true`, `commit_docs: true`

### Secundárias (MEDIUM confidence — múltiplas fontes concordantes)

- [stitch-mcp GitHub (davideast)](https://github.com/davideast/stitch-mcp) — Tools: `get_screen`, `generate_screen_from_text`, `list_projects`, `list_screens`, `edit_screens`, `generate_variants`, `create_project`, `get_project`
- [Stitch MCP npm `@_davideast/stitch-mcp`](https://www.npmjs.com/package/@_davideast/stitch-mcp) — Configuração do MCP server, uso de proxy
- [Google Codelabs: Design-to-Code com Stitch MCP](https://codelabs.developers.google.com/design-to-code-with-antigravity-stitch?hl=en) — Workflow oficial de extração e integração
- [Stitch documentation (stitch.withgoogle.com/docs)](https://stitch.withgoogle.com/docs) — Confirmado via playwright-cli capture

### Terciárias (LOW confidence — verificação pendente)

- Conteúdo exato dos designs Stitch para este projeto — não acessados (requer API key)
- Versão atual do MCP e compatibilidade com STITCH_API_KEY — requer teste real no ambiente

---

## Metadata

**Breakdown de confiança:**
- Stack e design system atual: HIGH — verificado diretamente no codebase
- Diagnóstico de `/recommend`: HIGH — lido todo o arquivo, classes hardcoded confirmadas
- Stitch MCP workflow e tools: MEDIUM — múltiplas fontes concordantes, não testado no projeto
- Conteúdo dos designs Stitch: LOW — projeto requer API key para acesso
- Pitfalls de implementação: MEDIUM-HIGH — pitfall de E2E regressão confirmado por análise dos specs existentes

**Data da pesquisa:** 2026-03-23
**Válido até:** 2026-04-23 (Stitch é produto em evolução rápida — verificar changelog ao iniciar)
