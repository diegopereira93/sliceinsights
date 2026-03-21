# Phase 15: AI Recommendation Assistant - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Quiz de perfil do jogador (`/recommend`) retorna até 3 raquetes recomendadas do catálogo ao vivo, com justificativa técnica (dossier LLM) e links de compra nas lojas brasileiras. Inclui chat pós-recomendação com a IA comentando as escolhas. Criação ou edição de dados do catálogo está fora do escopo.

</domain>

<decisions>
## Implementation Decisions

### API — Endpoint de recomendação
- Novo arquivo: `app/api/endpoints/recommend.py` com `APIRouter(prefix="/recommend")`
- Registrar em `app/main.py` como `recommend_router` (mesmo padrão de `catalog_router`)
- `POST /api/v1/recommend` — recebe `RecommendationRequest`, retorna `RecommendationResult` enriquecido com `market_offers`
- `POST /api/v1/recommend/chat` — recebe `ChatRequest`, retorna `ChatResponse`
- Endpoint público (sem auth) — padrão estabelecido nas fases anteriores
- Rate limiting: `@limiter.limit("30/minute")` no `/recommend` (mais restrito que catalog, pois chama LLM)

### API — Resposta enriquecida com links de compra (REC-02)
- `PaddleRecommendation` atual tem `min_price_brl` mas **não** tem `market_offers`
- Adicionar `market_offers: list[MarketOfferOut]` ao schema `PaddleRecommendation`, onde `MarketOfferOut = {store_name, price_brl, store_url}`
- `store_url` passa pelo `AffiliateService.transform_url()` antes de ser retornado
- Retornar **todas as ofertas ativas** de cada raquete, ordenadas por `price_brl` ASC
- Requer que `RecommendationEngine` carregue `market_offers` com `selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store)` (mesmo padrão do catalog endpoint)

### API — No-match behavior (REC-01 success criteria 4)
- Engine já faz budget relaxation automático (`fallback` query sem limite de orçamento)
- Se `len(recommendations) == 0` após fallback: LLM gera mensagem amigável via `generate_dossier()` com contexto vazio — ex: "Nenhuma raquete encontrada dentro do orçamento R$X. A mais próxima custa R$Y — considere ajustar o orçamento."
- Retornar `recommendations: []` + `grok_dossier: <mensagem_llm>` (não erro HTTP)

### Frontend — Rota e wizard
- Nova rota: `frontend/app/recommend/page.tsx` (URL `/recommend`)
- Wizard de 3 steps no mesmo componente (estado local com `useState`):
  - **Step 1**: `skill_level` (beginner/intermediate/advanced) + `play_style` (power/control/balanced)
  - **Step 2**: `budget_max_brl` (slider ou input numérico, opcional — botão "Sem limite")
  - **Step 3**: `has_tennis_elbow` (toggle) + `weight_preference` (heavy/standard/light/no_preference, opcional)
- CTA no `/catalog`: botão/banner "Não sabe qual raquete? Responda 3 perguntas" linkando para `/recommend`
- Dark mode: `bg-[#000000]`, accent `#ceff00` (lime), border `#222222` — padrão Phase 14

### Frontend — Tela de resultado (após submit do wizard)
- 3 cards de raquete exibidos na mesma página (substitui o wizard via estado)
- **1º card** ("Match Perfeito"): card maior com borda accent `#ceff00`, badge "Match Perfeito"
- **2º e 3º cards**: cards menores, visualmente secundários
- Cada card contém: imagem da raquete, brand + model_name, specs relevantes (core_thickness_mm, surface_material), lista de lojas com `price_brl` e link clicável (store_url com affiliate)
- Loading state durante chamada à API: skeleton nos cards

### Frontend — Chat abre automaticamente ao fim do quiz
- Após os cards renderizarem, o **painel de chat abre automaticamente** (sem clique)
- A **primeira mensagem do assistente** é o `grok_dossier` retornado pela API (o LLM já comenta as 3 raquetes no dossier)
- Painel de chat: seção inline abaixo dos 3 cards, rolável, com input na base
- Histórico de chat: estado local (`useState<ChatMessage[]>`), inicializado com `[{role: "assistant", content: grok_dossier}]`
- Cada mensagem do usuário chama `POST /api/v1/recommend/chat` com o histórico + contexto das 3 raquetes recomendadas
- Chat limitado ao contexto das 3 raquetes do resultado (contexto injetado no system prompt via `ChatRequest.context`)

### Claude's Discretion
- Animação de transição wizard → resultado (fade, slide, ou sem animação)
- Estilo visual do input de chat (placeholder text, ícone de envio)
- Exact skeleton loading design
- Tratamento de erros de rede no frontend (toast ou mensagem inline)

</decisions>

<specifics>
## Specific Ideas

- Versão original já tinha chat abrindo automaticamente ao fim do quiz — manter essa ideia com os cards das raquetes + IA comentando ao vivo
- O `grok_dossier` da engine (gerado por `generate_ai_recommendations()`) já menciona as 3 raquetes por nome — usar diretamente como primeira mensagem do chat, sem processar
- AffiliateService já suporta Amazon BR e Mercado Livre — aplicar em todas as `store_url` antes de serializar a resposta

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements desta fase
- `.planning/REQUIREMENTS.md` §Recommend — Assistente de IA — REC-01, REC-02, REC-03

### Backend — serviços existentes (base da implementação)
- `app/services/recommendation_engine.py` — Engine completa: query, filtros, ranking, LLM ranking, dossier, cache
- `app/services/llm_service.py` — Groq (Llama 3.3-70b): `generate_ai_recommendations()`, `generate_dossier()`, `chat_with_context()`
- `app/services/affiliate_service.py` — `AffiliateService.transform_url()`, `get_affiliate_service()`

### Backend — schemas e modelos a estender
- `app/schemas/user_profile.py` — `UserProfile`, `RecommendationRequest`, `RecommendationResult`, `PaddleRecommendation`
- `app/schemas/chat.py` — `ChatRequest`, `ChatResponse`, `ChatMessage`
- `app/models/enums.py` — `SkillLevel`, `PlayStyle` enums

### Backend — padrões a replicar
- `app/api/endpoints/catalog.py` — Padrão de router, limiter, `get_session`, `selectinload` com market_offers
- `app/main.py` — Onde registrar `recommend_router` (seguir padrão `catalog_router`)
- `app/api/dependencies.py` — `get_session` dependency

### Frontend — padrões existentes
- `frontend/app/catalog/page.tsx` (Phase 14) — Stack, dark mode tokens, card patterns, Tailwind classes
- `frontend/tailwind.config.js` — Design tokens (bg `#000000`, accent `#ceff00`, border `#222222`)

### Histórico relevante
- `.planning/phases/13-catalog-api/13-CONTEXT.md` — Padrão de resposta com market_offers, `o.store.name` via selectinload
- `.planning/phases/14-web-catalog-page/14-CONTEXT.md` — Stack Next.js 14 + TypeScript + Tailwind, dark mode estabelecido

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/services/recommendation_engine.py` — `RecommendationEngine.get_recommendations(profile, limit, use_ai_ranking)`: o endpoint apenas instancia a engine com a session e chama esse método
- `app/services/llm_service.py` — `llm_service` (singleton): `chat_with_context(chat_history, context)` para o endpoint `/recommend/chat`
- `app/services/affiliate_service.py` — `get_affiliate_service()` singleton: chamar `transform_url(store_url)` ao serializar cada `market_offer`
- `app/api/endpoints/catalog.py` — Padrão exato de router + limiter + async endpoint a replicar

### Established Patterns
- Todos os endpoints são públicos (sem auth) — estabelecido Phase 9
- `@limiter.limit("100/minute")` via slowapi — replicar com `"30/minute"` no /recommend (LLM call)
- `selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store)` para carregar `o.store.name`
- Response shape `{"data": [...], "total": N}` para listas; objeto direto para recomendações

### Integration Points
- `app/main.py` — adicionar `from app.api.endpoints.recommend import router as recommend_router` + `app.include_router(recommend_router, prefix="/api/v1")`
- `frontend/app/catalog/page.tsx` — adicionar CTA para `/recommend`
- Engine já consulta catálogo ao vivo via `MarketOffer.is_active` — REC-03 atendido sem mudança

</code_context>

<deferred>
## Deferred Ideas

- Knowledge base RAG (ai_knowledge_base com pgvector) — infraestrutura existe mas não está em escopo: popular base com reviews/transcrições é trabalho separado
- Histórico de recomendações por usuário — requer auth, fora do escopo v3
- Comparação lado a lado de raquetes selecionadas pelo usuário — fase futura

</deferred>

---

*Phase: 15-ai-recommendation-assistant*
*Context gathered: 2026-03-21*
