# Phase 17: UI Redesign — Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Substituir o frontend atual (Next.js 14) pelo frontend redesenhado no Replit (`redesign-slice/artifacts/sliceinsights/`), que é uma SPA Vite + React 19 + Tailwind 4. Inclui reaproveitar o API client gerado por Orval/React Query. O backend FastAPI permanece; rotas faltantes (leads, chat) serão criadas nele. Chat promovido de painel flutuante para rota dedicada `/chat`.

</domain>

<decisions>
## Implementation Decisions

### Estratégia de frontend
- **D-01:** Substituir o Next.js inteiro pelo Vite SPA de `redesign-slice/artifacts/sliceinsights/` — sem portar componentes para dentro do Next.js
- **D-02:** Stack alvo: Vite + React 19 + Tailwind 4 + Wouter + React Query
- **D-03:** Perda de SSR é aceitável — SliceInsights é app de recomendação, não depende de SEO crítico

### Backend
- **D-04:** Manter FastAPI Python como único backend de produção — Express do redesign-slice é referência de contrato de API, não vai pra produção
- **D-05:** Rotas faltantes no FastAPI: `POST /leads` (captura de email/nome) e `POST /chat` (proxy para LLM existente)
- **D-06:** O API client do redesign-slice (`lib/api-client-react/`) apontará para o FastAPI, não para o Express

### Páginas incluídas nesta fase
- **D-07:** 4 páginas do redesign-slice são incluídas: Home (`/`), Quiz (`/recommend`), Stats (`/statistics`), Chat (`/chat`)
- **D-08:** Chat é reorganização de UI — a lógica já existe como painel flutuante pós-quiz; esta fase apenas promove para rota dedicada

### Reaproveitamento do redesign-slice
- **D-09:** Reaproveitar: `artifacts/sliceinsights/` (frontend completo) + `lib/api-client-react/` (hooks React Query gerados)
- **D-10:** Não reaproveitar nesta fase: `lib/db/` (Drizzle), `lib/api-spec/` (OpenAPI), `artifacts/api-server/` (Express)

### Claude's Discretion
- Estrutura de pastas do novo frontend dentro do projeto
- Configuração do Vite e Tailwind 4
- Como adaptar o API client para apontar para o FastAPI existente
- Estratégia de E2E (adaptar testes Playwright existentes para nova estrutura)

</decisions>

<specifics>
## Specific Ideas

- O redesign-slice tem `BattleContext.tsx` e `BattleOverlay.tsx` — componentes de gamificação não documentados. Avaliar se fazem parte do redesign ou são experimentos descartáveis.
- O Express server em `artifacts/api-server/src/routes/` serve como documentação viva das rotas esperadas — usar como referência de contrato ao implementar no FastAPI.
- Rotas do Express a replicar no FastAPI: `POST /quiz/recommend`, `POST /leads`, `POST /chat`, `GET /stats/*`

</specifics>

<canonical_refs>
## Canonical References

Downstream agents MUST read these before planning or implementing.

### Frontend redesenhado (fonte de verdade)
- `redesign-slice/artifacts/sliceinsights/src/` — Código-fonte completo do frontend Vite SPA
- `redesign-slice/artifacts/sliceinsights/package.json` — Dependências e scripts do frontend

### API client
- `redesign-slice/lib/api-client-react/src/` — Hooks React Query gerados + custom-fetch
- `redesign-slice/lib/api-zod/` — Schemas Zod para validação das respostas

### Contrato de API (referência para FastAPI)
- `redesign-slice/artifacts/api-server/src/routes/` — Rotas Express que definem o contrato esperado pelo frontend

### Backend existente
- `app/` — FastAPI Python (backend de produção que será mantido)

### Frontend atual (a ser substituído)
- `frontend/` — Next.js 14 (referência para features existentes e E2E tests)
- `frontend/e2e/` — Suite Playwright existente — adaptar para novo frontend

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/e2e/sliceinsights.spec.ts` + `recommendation-e2e.spec.ts`: Suite E2E completa — adaptar seletores para novo DOM
- `frontend/e2e/responsiveness.spec.ts`: Testes de viewport já criados no plano 17-01 — base para responsividade
- `redesign-slice/artifacts/mockup-sandbox/src/components/ui/`: Biblioteca shadcn completa com ~50 componentes — já disponível no frontend redesenhado

### Established Patterns
- Design system tokens: `#000000` background, `#ceff00` primary accent, glassmorphism cards — já definidos e implementados nos planos 17-01/02/03; o redesign-slice os consolida
- API client pattern: `setBaseUrl()` + `setAuthTokenGetter()` em `lib/api-client-react/src/custom-fetch.ts`

### Integration Points
- O novo frontend precisa apontar `BASE_URL` para o FastAPI (atualmente em `http://localhost:8002/api/v1` em dev)
- Chat flutuante atual vive em `frontend/components/` — lógica precisa ser extraída para a nova rota `/chat`
- Playwright config (`frontend/playwright.config.ts`) precisará de atualização de porta/URL base

</code_context>

<deferred>
## Deferred Ideas

- **Drizzle + PostgreSQL direto no frontend stack** — Útil se o Express virar backend principal; prematuro agora
- **OpenAPI spec + Orval codegen completo** — Vantajoso, mas requer que FastAPI exporte spec válida; fase separada
- **Battle mode (BattleContext/BattleOverlay)** — Funcionalidade de gamificação presente no redesign-slice; avaliar produto antes de implementar
- **PWA/offline support** — Vite facilita isso vs. Next.js; candidato natural para próxima fase

</deferred>

---

*Phase: 17-ui-redesign-com-stitch*
*Context gathered: 2026-03-23*
