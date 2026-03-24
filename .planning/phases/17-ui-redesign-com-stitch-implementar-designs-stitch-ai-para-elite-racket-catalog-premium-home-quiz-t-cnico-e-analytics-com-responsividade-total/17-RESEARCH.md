# Phase 17: UI Redesign — Migrar frontend Next.js para Vite SPA — Research

**Researched:** 2026-03-23
**Domain:** Frontend migration (Next.js 14 -> Vite 7 + React 19 + Tailwind 4 + Wouter), API contract bridging, FastAPI stats endpoints
**Confidence:** HIGH (all findings from direct source code inspection)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Substituir o Next.js inteiro pelo Vite SPA de `redesign-slice/artifacts/sliceinsights/` — sem portar componentes para dentro do Next.js
- **D-02:** Stack alvo: Vite + React 19 + Tailwind 4 + Wouter + React Query
- **D-03:** Perda de SSR é aceitável — SliceInsights é app de recomendação, não depende de SEO crítico
- **D-04:** Manter FastAPI Python como único backend de produção — Express do redesign-slice é referência de contrato de API, não vai pra produção
- **D-05:** Rotas faltantes no FastAPI: `POST /leads` (captura de email/nome) e `POST /chat` (proxy para LLM existente)
- **D-06:** O API client do redesign-slice (`lib/api-client-react/`) apontará para o FastAPI, não para o Express
- **D-07:** 4 páginas do redesign-slice são incluídas: Home (`/`), Quiz (`/recommend`), Stats (`/statistics`), Chat (`/chat`)
- **D-08:** Chat é reorganização de UI — a lógica já existe como painel flutuante pós-quiz; esta fase apenas promove para rota dedicada
- **D-09:** Reaproveitar: `artifacts/sliceinsights/` (frontend completo) + `lib/api-client-react/` (hooks React Query gerados)
- **D-10:** Não reaproveitar nesta fase: `lib/db/` (Drizzle), `lib/api-spec/` (OpenAPI), `artifacts/api-server/` (Express)

### Claude's Discretion
- Estrutura de pastas do novo frontend dentro do projeto
- Configuração do Vite e Tailwind 4
- Como adaptar o API client para apontar para o FastAPI existente
- Estratégia de E2E (adaptar testes Playwright existentes para nova estrutura)

### Deferred Ideas (OUT OF SCOPE)
- **Drizzle + PostgreSQL direto no frontend stack** — Útil se o Express virar backend principal; prematuro agora
- **OpenAPI spec + Orval codegen completo** — Vantajoso, mas requer que FastAPI exporte spec válida; fase separada
- **Battle mode (BattleContext/BattleOverlay)** — Funcionalidade de gamificação presente no redesign-slice; avaliar produto antes de implementar
- **PWA/offline support** — Vite facilita isso vs. Next.js; candidato natural para próxima fase
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UI-01 | Substituir frontend Next.js pelo Vite SPA do redesign-slice | Frontend completo existe em `redesign-slice/artifacts/sliceinsights/src/` com 4 páginas funcionais (Home, Quiz, Stats, Chat) |
| UI-02 | Reaproveitar API client Orval/React Query (`lib/api-client-react/`) | Client gerado existe com hooks completos; necessita adaptação de URL base e bridge de schemas |
| UI-03 | Criar rotas FastAPI faltantes: `POST /leads` e `POST /chat` | **AMBAS JÁ EXISTEM** no FastAPI — `/api/v1/leads` (routes.py) e `/api/v1/chat` (routes.py). O gap é somente de schema e rota de stats |
| UI-04 | 4 páginas: Home (/), Quiz (/recommend), Stats (/statistics), Chat (/chat) | Wouter define `/`, `/quiz`, `/chat`, `/stats` — precisam renomear para `/recommend`, `/statistics` |
| UI-05 | Testes E2E adaptados para novo frontend (porta, seletores, rotas) | Playwright config aponta para `BASE_URL` env var; precisa atualizar porta (3002→nova), rotas e seletores DOM |
</phase_requirements>

---

## Summary

A migração é um **transplante cirúrgico**: o frontend `redesign-slice/artifacts/sliceinsights/` é um SPA Vite completo com 4 páginas funcionais (Home, Quiz, Chat, Stats), componentes shadcn/ui, design system dark com tokens `#000000`/`#ceff00`, framer-motion, e Recharts para charts. Ele está estruturado como workspace pnpm com dependência em `@workspace/api-client-react`, um cliente React Query gerado por Orval que já define todos os hooks necessários.

O maior desafio não é o frontend em si — ele está pronto — mas a **ponte de schemas entre o cliente Orval e o FastAPI**. O cliente usa uma API imaginada pelo Express (com campos como `Paddle.id: number`, `name`, `brand`, `powerScore`, `controlScore`), enquanto o FastAPI retorna `PaddleMaster` com `id: UUID`, `model_name`, `brand_id/brand_name`, `power_rating`, `control_rating`. São schemas diferentes. Além disso, os endpoints de stats (`/api/stats/market`, `/api/stats/brands`, `/api/stats/hidden-gems`) e o endpoint de quiz (`/api/quiz/recommend`) **não existem no FastAPI** — precisam ser criados. Já `/api/leads` e `/api/chat` existem no FastAPI mas com contratos ligeiramente diferentes.

**Decisão primária:** Criar um `frontend-vite/` novo na raiz do projeto (ou substituir `frontend/` in-place), copiar o código do `redesign-slice/artifacts/sliceinsights/` com mínimas adaptações, ajustar o Vite config para remover dependências Replit, inicializar `setBaseUrl()` com `VITE_API_URL`, e criar uma camada thin de adaptação de schema no FastAPI (ou dentro do próprio cliente).

---

## Standard Stack

### Core (redesign-slice — já definido, usar exatamente estas versões)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| vite | ^7.3.0 | Build tool + dev server | Catálogo pnpm-workspace |
| react | 19.1.0 | UI framework | Catálogo pnpm-workspace |
| react-dom | 19.1.0 | DOM renderer | Catálogo pnpm-workspace |
| @vitejs/plugin-react | ^5.0.4 | React Fast Refresh | Catálogo pnpm-workspace |
| @tailwindcss/vite | ^4.1.14 | Tailwind 4 via Vite plugin | Catálogo pnpm-workspace |
| tailwindcss | ^4.1.14 | Utility CSS | Catálogo pnpm-workspace |
| wouter | ^3.3.5 | Client-side routing leve | devDependencies do sliceinsights |
| @tanstack/react-query | ^5.90.21 | Async state / data fetching | Catálogo pnpm-workspace |
| framer-motion | 12.35.1 | Animações | Catálogo pnpm-workspace — versão exata fixada |
| recharts | ^2.15.4 | Charts (Stats page) | devDependencies do sliceinsights |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | ^0.545.0 | Ícones | Já usado nas 4 páginas |
| @radix-ui/* | ^1.x-^2.x | Primitivos UI acessíveis | Base para shadcn/ui components |
| zod | ^3.25.76 | Validação de schemas | Catálogo pnpm-workspace |
| clsx + tailwind-merge | latest | className utilities | cn() helper já em uso |
| sonner | ^2.0.7 | Toast notifications | Usado via `<Toaster>` em App.tsx |

### Não instalar (dependências Replit — remover do Vite config)
- `@replit/vite-plugin-cartographer`
- `@replit/vite-plugin-dev-banner`
- `@replit/vite-plugin-runtime-error-modal`

**Installation (novo frontend standalone):**
```bash
# Opção A: pnpm workspace (manter estrutura redesign-slice)
# já instalado em redesign-slice/

# Opção B: standalone em frontend-vite/ (recomendado — isola do workspace Replit)
npm create vite@latest frontend-vite -- --template react-ts
cd frontend-vite && npm install
# Copiar src/ do redesign-slice, instalar deps manualmente
```

---

## Architecture Patterns

### Recommended Project Structure

A estrutura recomendada é substituir `frontend/` inteiramente por um novo diretório `frontend-vite/` (standalone, sem workspace pnpm), copiando o código-fonte do redesign-slice:

```
frontend-vite/
├── src/
│   ├── pages/
│   │   ├── Home.tsx          # Catálogo + filtros smart
│   │   ├── Quiz.tsx          # 4 steps + lead gate + resultado
│   │   ├── Chat.tsx          # AI Coach chat interface
│   │   ├── Stats.tsx         # Market stats + charts
│   │   └── not-found.tsx
│   ├── components/
│   │   ├── ui/               # shadcn components (~50 componentes)
│   │   ├── BottomNav.tsx     # Navegação mobile
│   │   ├── PaddleCard.tsx    # Card de raquete
│   │   ├── BattleContext.tsx # (incluir mas não ativar — D-10 deferred)
│   │   └── BattleOverlay.tsx # (incluir mas não ativar — D-10 deferred)
│   ├── lib/
│   │   ├── api-client/       # custom-fetch.ts + hooks gerados (copiado de redesign-slice/lib/api-client-react/src/)
│   │   └── utils.ts          # cn(), formatCurrency()
│   ├── hooks/                # Custom hooks se existirem
│   ├── App.tsx               # Wouter router + QueryClientProvider
│   ├── main.tsx              # Entry point + setBaseUrl()
│   └── index.css             # Tailwind 4 + design system tokens
├── public/
│   └── images/               # cinematic-paddle-nobg.png, ai-avatar.png
├── vite.config.ts            # Adaptado (sem plugins Replit, PORT/BASE_PATH simples)
├── tailwind.config.ts        # Se necessário (Tailwind 4 usa CSS-first config)
├── tsconfig.json
└── package.json
```

### Pattern 1: API Client Bootstrap — setBaseUrl() em main.tsx

O `custom-fetch.ts` usa um módulo-level `_baseUrl` configurável via `setBaseUrl()`. O frontend precisa chamar isso antes do primeiro render:

```typescript
// src/main.tsx
import { setBaseUrl } from "./lib/api-client/custom-fetch";
import App from "./App";
import { createRoot } from "react-dom/client";

// Resolve API URL: env var em build time, ou default para dev
const apiBase = import.meta.env.VITE_API_URL ?? "http://localhost:8002/api/v1";
setBaseUrl(apiBase);

createRoot(document.getElementById("root")!).render(<App />);
```

```bash
# .env.local (dev)
VITE_API_URL=http://localhost:8002/api/v1

# .env.production
VITE_API_URL=https://sliceinsights-4rmf.onrender.com/api/v1
```

### Pattern 2: Wouter Router — Rotas a renomear

O App.tsx do redesign-slice usa `/quiz`, `/stats`. O plano exige `/recommend` e `/statistics` (D-07). Alteração mínima no App.tsx:

```typescript
// App.tsx — rotas conforme D-07
<Route path="/" component={Home} />
<Route path="/recommend" component={Quiz} />      // era /quiz
<Route path="/statistics" component={Stats} />    // era /stats
<Route path="/chat" component={Chat} />
<Route component={NotFound} />
```

O `BottomNav.tsx` também precisa ter seus links atualizados de `/quiz` → `/recommend` e `/stats` → `/statistics`.

### Pattern 3: Adaptação do Vite Config para standalone

O `vite.config.ts` do redesign-slice **requer** `PORT` e `BASE_PATH` como env vars obrigatórias (joga erro se ausentes) e usa plugins Replit. Para standalone:

```typescript
// vite.config.ts — adaptado para fora do Replit
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  server: { port: 3002, host: "0.0.0.0" },
  build: { outDir: "dist" },
});
```

### Pattern 4: Schema Bridge — Como lidar com a incompatibilidade Paddle

O cliente Orval espera `Paddle` com campos do Express schema:
- `id: number`, `name: string`, `brand: string`, `powerScore: number`, `controlScore: number`, `price: number`, `shopUrl?: string`, `isHiddenGem?: boolean`

O FastAPI retorna `PaddleRead` com:
- `id: UUID`, `model_name: string`, `brand_name: string`, `power_rating: int | null`, `control_rating: int | null`, `min_price: float | null`, `market_offers: [...]`

**Estratégia recomendada (Claude's Discretion):** Criar endpoints de shim no FastAPI que retornam o schema esperado pelo cliente Orval:
- `GET /api/paddles` — retorna `PaddleListResponse { paddles: Paddle[], total: number }` mapeando campos
- `GET /api/paddles/{id}` — retorna `Paddle` com id numérico (usar `id_seq` ou hash de UUID)
- `GET /api/quiz/recommend` — novo endpoint que mapeia `QuizAnswers` → `RecommendationRequest` e retorna `QuizRecommendation`
- `GET /api/stats/market`, `GET /api/stats/brands`, `GET /api/stats/hidden-gems` — novos endpoints de stats

**Alternativa:** Fazer o frontend consumir a API FastAPI diretamente (reescrever hooks) — mais trabalhoso mas elimina shim layer.

### Anti-Patterns to Avoid

- **Usar pnpm workspace do redesign-slice diretamente:** O workspace tem overrides agressivos de plataforma (esbuild, rollup, lightningcss) para o Replit. Fora do Replit vai falhar no `pnpm install`. Copiar o código como standalone.
- **Manter `PORT` e `BASE_PATH` obrigatórios:** O vite.config.ts do redesign-slice joga `throw new Error` se não tiver essas vars. Remover obrigatoriedade.
- **Tentar usar `@workspace/api-client-react` como pacote pnpm externo:** Sem o workspace, esse import quebra. Copiar o código-fonte diretamente para `src/lib/api-client/`.
- **Configurar CORS no FastAPI sem incluir a nova porta:** A lista `allowed_origins` hardcoded em `app/config.py` precisa incluir `http://localhost:3002` (já está) e qualquer nova porta do Vite.
- **Esquecer de remover `next-themes`:** O redesign-slice usa `next-themes ^0.4.6` — verificar se está em uso nas páginas (não detectado nas páginas lidas). Se não usado, remover.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Routing SPA | React Router custom | Wouter (já no redesign-slice) | Wouter é mínimo e já integrado em App.tsx + links |
| React Query hooks | Fetch wrappers manuais | `@workspace/api-client-react` hooks gerados | Hooks já gerados por Orval com tipagem completa |
| CSS utility merging | Lógica custom de className | `clsx` + `tailwind-merge` via `cn()` | Já existe em `src/lib/utils.ts` do redesign-slice |
| Animações | CSS transitions manuais | `framer-motion` (versão 12.35.1 fixada) | Já usado em todas as 4 páginas |
| Charts | Canvas direto ou D3 | `recharts` | Já integrado em Stats.tsx com ScatterChart e BarChart |
| Docker frontend | Nginx custom config | Node serve estático | Vite build gera SPA estática — nginx ou `vite preview` |

**Key insight:** Todo o código de UI já existe no redesign-slice. O trabalho real é a adaptação de infraestrutura (Vite config, CORS, Docker) e a ponte de schemas entre o cliente Orval e a API FastAPI real.

---

## Common Pitfalls

### Pitfall 1: Incompatibilidade de Schema — Paddle.id number vs UUID

**What goes wrong:** O cliente Orval define `Paddle.id: number` e todos os hooks que recebem `id` (ex: `useGetPaddle(id: number)`) vão quebrar com UUIDs do FastAPI.

**Why it happens:** O schema Orval foi gerado a partir do OpenAPI do Express (que usa IDs numéricos no Drizzle), não do FastAPI (que usa `UUID`).

**How to avoid:** Nos endpoints de shim FastAPI, retornar um `id` numérico (ex: via sequência PostgreSQL ou hash) ou atualizar o schema Orval para aceitar string/UUID. A forma mais simples: adicionar uma coluna `id_legacy: int` serial no `PaddleMaster` ou usar `DENSE_RANK()` na query de listagem.

**Warning signs:** TypeScript vai reclamar imediatamente se o tipo não bater.

### Pitfall 2: Vite Config com vars obrigatórias do Replit

**What goes wrong:** `vite.config.ts` do redesign-slice joga `throw new Error("PORT environment variable is required")` antes de exportar a config. `npm run dev` vai falhar imediatamente.

**Why it happens:** O config foi escrito para o ambiente Replit que injeta `PORT` e `BASE_PATH` automaticamente.

**How to avoid:** Reescrever o vite.config.ts removendo as validações obrigatórias e os plugins Replit (`@replit/vite-plugin-*`). Usar porta fixa 3002 ou `process.env.PORT || 3002`.

**Warning signs:** Erro na inicialização do `vite dev` antes de qualquer compilação.

### Pitfall 3: Workspace pnpm incompatível fora do Replit

**What goes wrong:** O `pnpm-workspace.yaml` do redesign-slice tem overrides de plataforma específicos do Replit (remove binários para arm, darwin, freebsd). Em ambiente Linux/Mac de dev pode quebrar ou instalar versões erradas de esbuild/rollup.

**Why it happens:** O workspace foi configurado para o sandbox Replit (Linux x64).

**How to avoid:** Não usar o workspace pnpm do redesign-slice. Copiar o código para `frontend-vite/` e criar um `package.json` standalone limpo com as dependências necessárias.

### Pitfall 4: Endpoints de stats inexistentes no FastAPI

**What goes wrong:** `Stats.tsx` chama `useGetMarketStats()` (→ `GET /api/stats/market`) e `useGetBrandStats()` (→ `GET /api/stats/brands`). Esses endpoints **não existem** no FastAPI hoje.

**Why it happens:** O FastAPI foi construído para o frontend Next.js anterior, que não tinha página de Stats no mesmo formato.

**How to avoid:** Criar os 3 endpoints de stats no FastAPI antes de ativar a página Stats: `GET /api/v1/stats/market`, `GET /api/v1/stats/brands`, `GET /api/v1/stats/hidden-gems`. Os dados necessários existem no banco (PaddleMaster + MarketOffer).

**Warning signs:** Stats page fica em loading infinito ou mostra `if (!marketStats) return null` sem renderizar nada.

### Pitfall 5: Endpoint `/api/quiz/recommend` inexistente no FastAPI

**What goes wrong:** `Quiz.tsx` chama `useGetQuizRecommendation()` (→ `POST /api/quiz/recommend`). O FastAPI tem `POST /api/v1/recommendations` e `POST /api/v1/recommend` (via recommend_router), mas **não** `/api/quiz/recommend`.

**Why it happens:** O Orval foi gerado a partir do contrato Express, que usa `/quiz/recommend`.

**How to avoid:** Criar um endpoint de alias `POST /api/v1/quiz/recommend` no FastAPI que adapte `QuizAnswers` (budget como string: "under300") para `RecommendationRequest` (budget_max_brl: float) e retorne `QuizRecommendation` (topPick + alternatives + reasoning).

### Pitfall 6: Schema de Chat divergente

**What goes wrong:** O cliente Orval envia `ChatMessageInput { message: string, conversationHistory: [...], recommendedPaddleId?: number }` mas o FastAPI `ChatRequest` espera `{ messages: [{role, content}], context: string, paddle_id?: UUID }`.

**Why it happens:** Contratos completamente diferentes — Express usa campo único `message` + histórico separado, FastAPI usa lista completa de mensagens + context string.

**How to avoid:** Criar um endpoint de shim `POST /api/v1/chat` que aceite o schema Orval e adapte para a lógica interna. O FastAPI já tem `/api/v1/chat` (em routes.py) com o schema FastAPI. Criar um segundo endpoint `/api/v1/chat` com schema Orval substituindo o existente, ou unificar os schemas.

### Pitfall 7: Imagens estáticas dependem de BASE_URL do Vite

**What goes wrong:** `Home.tsx` usa `${import.meta.env.BASE_URL}images/cinematic-paddle-nobg.png`. Se `BASE_URL` não estiver configurado ou as imagens não estiverem em `public/images/`, vai mostrar imagem quebrada.

**Why it happens:** As imagens ficam em `attached_assets/` no workspace Replit mas precisam estar em `public/` no Vite standalone.

**How to avoid:** Copiar as imagens de `redesign-slice/attached_assets/` para `frontend-vite/public/images/`.

### Pitfall 8: BattleContext + BattleOverlay em App.tsx

**What goes wrong:** `App.tsx` wrapa tudo em `<BattleProvider>` e renderiza `<BattleOverlay>`. Battle mode está deferido (D-10), mas o código está no App.tsx — se mantido, requer que BattleContext e BattleOverlay compilem sem erros.

**Why it happens:** Funcionalidade presente no redesign-slice mas não documentada como feature produto.

**How to avoid:** Manter os componentes mas verificar se compilam sem erros. Se causarem dependências problemáticas, remover o `<BattleProvider>` e `<BattleOverlay>` do App.tsx nesta fase (não há rota ativada para eles de qualquer forma).

---

## API Contract Analysis

### Endpoints esperados pelo cliente Orval vs FastAPI atual

| Endpoint Orval | Método | Existe no FastAPI? | Ação necessária |
|----------------|--------|-------------------|-----------------|
| `/api/healthz` | GET | NÃO (FastAPI tem `/api/v1/health`) | Criar alias ou atualizar URL no cliente |
| `/api/paddles` | GET | SIM (`/api/v1/paddles`) — mas schema diferente | Criar shim ou adaptador de resposta |
| `/api/paddles/{id}` | GET | SIM (`/api/v1/paddles/{uuid}`) — id type diferente | Adapter |
| `/api/quiz/recommend` | POST | NÃO | Criar `POST /api/v1/quiz/recommend` |
| `/api/leads` | POST | SIM (`/api/v1/leads`) — schema levemente diferente | Verificar compatibilidade |
| `/api/chat` | POST | SIM (`/api/v1/chat`) — schema diferente | Criar shim ou unificar schema |
| `/api/stats/market` | GET | NÃO | Criar `GET /api/v1/stats/market` |
| `/api/stats/brands` | GET | NÃO | Criar `GET /api/v1/stats/brands` |
| `/api/stats/hidden-gems` | GET | NÃO | Criar `GET /api/v1/stats/hidden-gems` |

**Observação crítica:** O cliente Orval usa paths sem prefixo `/v1/` — chama `/api/paddles`, não `/api/v1/paddles`. Isso significa que o `setBaseUrl()` precisa ser chamado com a URL base SEM o `/v1`, ou os URLs gerados precisam incluir `/v1`.

Analisando o código gerado:
- `getListPaddlesUrl()` → `/api/paddles`
- `getCaptureLeadUrl()` → `/api/leads`
- `getSendChatMessageUrl()` → `/api/chat`
- `getGetMarketStatsUrl()` → `/api/stats/market`

E `setBaseUrl` é chamado com `http://localhost:8002/api/v1` por intenção (conforme CONTEXT.md). Mas o `applyBaseUrl` em custom-fetch.ts só prepend para paths que começam com `/`. Então a URL final seria: `http://localhost:8002/api/v1/api/paddles` — **ERRADO**.

**Solução:** `setBaseUrl("http://localhost:8002")` — sem o `/api/v1` — e criar novos routes no FastAPI com prefix `/api/paddles`, `/api/leads`, `/api/chat`, `/api/stats/*`. Alternativamente, manter `/api/v1` no baseUrl e ter o cliente gerar URLs `/v1/paddles` — o que requer regenerar o Orval.

**Recomendação (Claude's Discretion):** Registrar um router FastAPI adicional com prefix `/api` (sem v1) que serve os endpoints no formato Orval. Isso preserva o cliente sem regeneração.

### Leads — Compatibilidade de Schema

Orval envia: `{ name: string, email: string, quizAnswers?: QuizAnswers, recommendedPaddleId?: number }`
FastAPI `LeadCreate` aceita: `{ email: EmailStr, name?: str, converted_from?: str }`

Os campos `quizAnswers` e `recommendedPaddleId` não existem no `LeadCreate`. FastAPI com `extra = "ignore"` (config.py tem isso) vai simplesmente ignorar campos extras. Compatível sem mudança de schema, desde que `name` seja enviado (FastAPI o aceita como opcional).

**Porém:** `LeadResponse` do Orval espera `{ success: boolean, message: string }` mas FastAPI retorna `LeadRead { id: int, email: str, name: str, created_at: datetime }`. Isso vai causar erro de parsing no cliente.

---

## Code Examples

### Bootstrap do API Client em main.tsx

```typescript
// frontend-vite/src/main.tsx
import React from "react";
import { createRoot } from "react-dom/client";
import { setBaseUrl } from "./lib/api-client/custom-fetch";
import App from "./App";
import "./index.css";

// Base URL aponta para FastAPI sem prefixo /api/v1
// Os paths gerados pelo Orval já incluem /api/...
const apiBase = import.meta.env.VITE_API_URL ?? "http://localhost:8002";
setBaseUrl(apiBase);

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

### Novo endpoint FastAPI — /api/paddles (shim Orval)

```python
# app/api/endpoints/orval_shim.py
from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.database import get_session
from app.models import PaddleMaster, MarketOffer
from typing import Optional

router = APIRouter(prefix="/api", tags=["orval-shim"])

@router.get("/paddles")
async def list_paddles_orval(
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    brand: Optional[str] = None,
    minPrice: Optional[float] = None,
    maxPrice: Optional[float] = None,
    coreThickness: Optional[float] = None,
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    """Orval-compatible paddle listing. Maps PaddleMaster to Paddle schema."""
    # ... query PaddleMaster, join MarketOffer for min_price ...
    # ... map to Orval Paddle schema: id=seq_id, name=model_name, brand=brand.name ...
    pass
```

### Endpoint de stats — /api/stats/market

```python
# Dentro de orval_shim.py ou stats router
@router.get("/stats/market")
async def get_market_stats(session: AsyncSession = Depends(get_session)):
    """Market stats compatible with Orval MarketStats schema."""
    paddles = await session.exec(select(PaddleMaster).options(selectinload(PaddleMaster.brand)))
    all_paddles = paddles.all()

    # Calcular total, avgPrice, distribuições
    # Retornar no formato MarketStats do Orval:
    # { totalPaddles, averagePrice, bestValue, topPower,
    #   coreThicknessDistribution, priceRangeDistribution, powerVsControlData }
    pass
```

### Dockerfile.frontend — Adaptado para Vite

```dockerfile
# Dockerfile.frontend (substituir versão Next.js)
FROM node:20-alpine AS builder
WORKDIR /app

COPY frontend-vite/package*.json ./
RUN npm ci

COPY frontend-vite/ .
ARG VITE_API_URL=http://localhost:8002
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM nginx:alpine AS runner
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend-vite/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# frontend-vite/nginx.conf — SPA fallback para Wouter
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### docker-compose.yml — Serviço frontend atualizado

```yaml
# Substituir frontend_next por frontend_vite no docker-compose.yml
frontend_vite:
  build:
    context: .
    dockerfile: Dockerfile.frontend
    args:
      VITE_API_URL: http://backend_v3:8000
  container_name: picklematch_ui_vite
  ports:
    - "3002:80"
  depends_on:
    - backend_v3
  networks:
    - picklematch_v3
  restart: unless-stopped
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Next.js 14 App Router + SSR | Vite 7 SPA + Wouter | Esta fase | Sem SSR; build estático servido por nginx |
| React 18.3 | React 19.1.0 | Esta fase | `use()` hook, concurrent features melhoradas |
| Tailwind CSS 3 (PostCSS plugin) | Tailwind CSS 4 (Vite plugin) | Esta fase | CSS-first config; `@import "tailwindcss"` no index.css; sem tailwind.config.js obrigatório |
| NEXT_PUBLIC_API_URL (build-time) | VITE_API_URL (build-time) | Esta fase | Mesma semântica, prefix diferente |
| Next.js server-side API proxy | CORS direto para FastAPI | Esta fase | CORS deve estar habilitado no FastAPI (já está) |
| Playwright porta 3002 baseURL | Playwright nova porta/URL | Esta fase | Atualizar `playwright.config.ts` baseURL e e2e scripts |

**Deprecated/outdated nesta migração:**
- `Dockerfile.frontend` atual: usa Next.js multi-stage com `node server.js` — substituir por nginx estático
- `docker-compose.yml` serviço `frontend_next`: renomear para `frontend_vite`, mudar build e porta
- `frontend/playwright.config.ts` baseURL: atualizar porta e remover referência a Next.js
- `frontend/package.json` scripts `test:e2e:local`: atualizar `BASE_URL` porta

---

## Deployment & Integration Changes

### Arquivos que precisam ser modificados

| Arquivo | Mudança necessária |
|---------|-------------------|
| `Dockerfile.frontend` | Reescrever para Vite + nginx estático |
| `docker-compose.yml` | Serviço `frontend_next` → `frontend_vite`, porta, build args |
| `docker-compose.prod.yml` | Idem para produção |
| `app/config.py` `allowed_origins` | Adicionar nova porta Vite se diferente de 3002 |
| `app/main.py` | Incluir novo router `/api` (shim Orval) |
| `frontend/playwright.config.ts` | Mover para `frontend-vite/` ou atualizar `testDir` e `baseURL` |

### Arquivos que NÃO mudam
- `app/` — FastAPI permanece; só adiciona novos endpoints
- `docker-compose.yml` serviços `postgres_v3` e `backend_v3`
- `.env` / secrets de produção

---

## Open Questions

1. **Localização do novo frontend: `frontend-vite/` (novo) ou substituir `frontend/` in-place?**
   - O que sabemos: branch atual `feat/phase-17-ui-redesign-stitch` tem changes em `frontend/` (planos 17-01 a 17-04 modificaram o Next.js)
   - O que está incerto: se os planos 17-01/02/03/04 já implementados representam trabalho a preservar ou serão descartados com a migração
   - Recomendação: Criar `frontend-vite/` novo, manter `frontend/` intocado até validação E2E passar no novo frontend

2. **IDs numéricos vs UUIDs — qual estratégia de shim adotar?**
   - O que sabemos: Orval usa `Paddle.id: number`; FastAPI usa `UUID`; não existe `id_legacy` serial no PaddleMaster
   - O que está incerto: Se PaddleCard.tsx no redesign-slice usa `id` para navegação ou apenas para key de React
   - Recomendação: Usar `DENSE_RANK() OVER (ORDER BY created_at)` na query ou adicionar migração Alembic com `id_seq SERIAL` — investigar uso de `id` nas páginas antes de decidir

3. **Stats endpoint — `isHiddenGem` e `powerScore`/`controlScore` não existem no PaddleMaster?**
   - O que sabemos: PaddleMaster tem `power_rating: int | None` e `control_rating: int | None`, não `powerScore`/`controlScore`; não tem `isHiddenGem`
   - O que está incerto: Se há alguma coluna equivalente ou se precisa ser derivada (ex: `is_featured` como proxy)
   - Recomendação: Mapear `powerScore = power_rating`, `controlScore = control_rating` no shim; derivar `isHiddenGem = is_featured == False AND power_rating >= 8` ou similar

4. **Imagens estáticas — onde ficam no contexto do projeto?**
   - O que sabemos: `Home.tsx` usa `cinematic-paddle-nobg.png`, `Chat.tsx` usa `ai-avatar.png` — ambas em `redesign-slice/attached_assets/`
   - O que está incerto: Se essas imagens existem ou precisam ser criadas/obtidas
   - Recomendação: Verificar `ls redesign-slice/attached_assets/` antes de planejar

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Playwright 1.58.2 (já instalado em `frontend/`) |
| Config file | `frontend/playwright.config.ts` — mover/copiar para `frontend-vite/playwright.config.ts` |
| Quick run command | `BASE_URL=http://localhost:3002 npx playwright test --reporter=list --project=desktop` |
| Full suite command | `BASE_URL=http://localhost:3002 API_URL=http://localhost:8002/api/v1 npx playwright test --reporter=list` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | Página Home carrega e exibe paddle cards | e2e | `npx playwright test sliceinsights.spec.ts -k "displays paddle cards"` | Adaptar de `frontend/e2e/sliceinsights.spec.ts` |
| UI-01 | Página Chat acessível em `/chat` | e2e | `npx playwright test sliceinsights.spec.ts -k "chat"` | Wave 0 — novo |
| UI-02 | API client faz chamada para FastAPI corretamente | integration | `npx playwright test recommendation-e2e.spec.ts` | Adaptar de `frontend/e2e/recommendation-e2e.spec.ts` |
| UI-03 | POST /api/leads retorna sucesso | smoke | `npx playwright test sliceinsights.spec.ts -k "lead"` | Wave 0 — novo |
| UI-03 | POST /api/chat retorna reply | smoke | `npx playwright test sliceinsights.spec.ts -k "chat reply"` | Wave 0 — novo |
| UI-04 | Rota /recommend renderiza Quiz | e2e | `npx playwright test sliceinsights.spec.ts -k "quiz"` | Adaptar seletores |
| UI-04 | Rota /statistics renderiza Stats | e2e | `npx playwright test sliceinsights.spec.ts -k "stats"` | Wave 0 — novo |
| UI-05 | Layout responsivo mobile/tablet/desktop | e2e | `npx playwright test responsiveness.spec.ts` | Adaptar de `frontend/e2e/responsiveness.spec.ts` |

### Sampling Rate
- **Per task commit:** `BASE_URL=http://localhost:3002 npx playwright test --reporter=list --project=desktop -k "Homepage"` (smoke rápido)
- **Per wave merge:** `BASE_URL=http://localhost:3002 npx playwright test --reporter=list` (suite completa)
- **Phase gate:** Full suite green (desktop + mobile + tablet) antes de `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `frontend-vite/playwright.config.ts` — copiar e adaptar de `frontend/playwright.config.ts` (baseURL porta, testDir)
- [ ] `frontend-vite/e2e/sliceinsights.spec.ts` — adaptar seletores para novo DOM Vite (rota `/recommend` vs `/quiz`, `/statistics` vs `/stats`)
- [ ] `frontend-vite/e2e/responsiveness.spec.ts` — copiar de `frontend/e2e/responsiveness.spec.ts` com paths atualizados
- [ ] `frontend-vite/e2e/recommendation-e2e.spec.ts` — adaptar para novo schema de resposta FastAPI shim
- [ ] Teste de smoke para `/api/stats/market` e `/api/stats/brands` — verificar endpoints existem antes do frontend
- [ ] Framework install: `npm install --save-dev @playwright/test` em `frontend-vite/` (ou herdar do `frontend/`)

---

## Sources

### Primary (HIGH confidence)
- Leitura direta de `redesign-slice/artifacts/sliceinsights/src/` — páginas, App.tsx, componentes
- Leitura direta de `redesign-slice/lib/api-client-react/src/generated/api.ts` e `api.schemas.ts` — todos os endpoints e tipos
- Leitura direta de `redesign-slice/lib/api-client-react/src/custom-fetch.ts` — mecanismo setBaseUrl
- Leitura direta de `app/api/routes.py` — todos os endpoints FastAPI existentes
- Leitura direta de `app/api/endpoints/recommend.py`, `catalog.py` — endpoints adicionais
- Leitura direta de `app/main.py` — prefixos de router, CORS, middleware
- Leitura direta de `app/config.py` — allowed_origins
- Leitura direta de `app/models/paddle.py`, `app/models/lead.py`, `app/schemas/chat.py`, `app/schemas/user_profile.py` — schemas FastAPI
- Leitura direta de `redesign-slice/artifacts/api-server/src/routes/` — contrato Express (stats, quiz, leads, chat)
- Leitura direta de `redesign-slice/pnpm-workspace.yaml` — versões exatas do catálogo
- Leitura direta de `docker-compose.yml`, `Dockerfile.frontend` — configuração atual de deploy
- Leitura direta de `frontend/playwright.config.ts` — configuração E2E atual
- Leitura direta de `.planning/config.json` — `nyquist_validation: true`

### Secondary (MEDIUM confidence)
- Análise de compatibilidade React 19 + framer-motion 12.35.1 — versão fixada no catálogo, sem verificação de changelog

### Tertiary (LOW confidence)
- Nenhum item exclusivamente de WebSearch

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versões lidas diretamente do pnpm-workspace.yaml catálogo
- Architecture: HIGH — estrutura de código inspecionada diretamente
- API contract gaps: HIGH — endpoints comparados linha a linha entre Orval e FastAPI
- Pitfalls: HIGH — todos derivados de incompatibilidades concretas encontradas no código
- Deployment changes: HIGH — Dockerfile e docker-compose lidos diretamente

**Research date:** 2026-03-23
**Valid until:** 2026-04-22 (30 dias — stack estável)
