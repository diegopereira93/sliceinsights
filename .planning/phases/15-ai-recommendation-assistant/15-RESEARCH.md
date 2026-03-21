# Phase 15: AI Recommendation Assistant - Research

**Researched:** 2026-03-21
**Domain:** FastAPI endpoint wiring + Next.js multi-step wizard + Groq LLM integration
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**API — Endpoint de recomendacao**
- Novo arquivo: `app/api/endpoints/recommend.py` com `APIRouter(prefix="/recommend")`
- Registrar em `app/main.py` como `recommend_router` (mesmo padrao de `catalog_router`)
- `POST /api/v1/recommend` — recebe `RecommendationRequest`, retorna `RecommendationResult` enriquecido com `market_offers`
- `POST /api/v1/recommend/chat` — recebe `ChatRequest`, retorna `ChatResponse`
- Endpoint publico (sem auth) — padrao estabelecido nas fases anteriores
- Rate limiting: `@limiter.limit("30/minute")` no `/recommend` (mais restrito que catalog, pois chama LLM)

**API — Resposta enriquecida com links de compra (REC-02)**
- `PaddleRecommendation` atual tem `min_price_brl` mas nao tem `market_offers`
- Adicionar `market_offers: list[MarketOfferOut]` ao schema `PaddleRecommendation`, onde `MarketOfferOut = {store_name, price_brl, store_url}`
- `store_url` passa pelo `AffiliateService.transform_url()` antes de ser retornado
- Retornar todas as ofertas ativas de cada raquete, ordenadas por `price_brl` ASC
- Requer que `RecommendationEngine` carregue `market_offers` com `selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store)` (mesmo padrao do catalog endpoint)

**API — No-match behavior (REC-01 success criteria 4)**
- Engine ja faz budget relaxation automatico (`fallback` query sem limite de orcamento)
- Se `len(recommendations) == 0` apos fallback: LLM gera mensagem amigavel via `generate_dossier()` com contexto vazio
- Retornar `recommendations: []` + `grok_dossier: <mensagem_llm>` (nao erro HTTP)

**Frontend — Rota e wizard**
- Nova rota: `frontend/app/recommend/page.tsx` (URL `/recommend`)
- Wizard de 3 steps no mesmo componente (estado local com `useState`):
  - Step 1: `skill_level` (beginner/intermediate/advanced) + `play_style` (power/control/balanced)
  - Step 2: `budget_max_brl` (slider ou input numerico, opcional — botao "Sem limite")
  - Step 3: `has_tennis_elbow` (toggle) + `weight_preference` (heavy/standard/light/no_preference, opcional)
- CTA no `/catalog`: botao/banner "Nao sabe qual raquete? Responda 3 perguntas" linkando para `/recommend`
- Dark mode: `bg-[#000000]`, accent `#ceff00` (lime), border `#222222` — padrao Phase 14

**Frontend — Tela de resultado (apos submit do wizard)**
- 3 cards de raquete exibidos na mesma pagina (substitui o wizard via estado)
- 1 card ("Match Perfeito"): card maior com borda accent `#ceff00`, badge "Match Perfeito"
- 2 e 3 cards: cards menores, visualmente secundarios
- Cada card: imagem da raquete, brand + model_name, specs relevantes, lista de lojas com `price_brl` e link clicável (store_url com affiliate)
- Loading state durante chamada a API: skeleton nos cards

**Frontend — Chat abre automaticamente ao fim do quiz**
- Apos os cards renderizarem, o painel de chat abre automaticamente (sem clique)
- A primeira mensagem do assistente e o `grok_dossier` retornado pela API
- Painel de chat: secao inline abaixo dos 3 cards, rolavel, com input na base
- Historico de chat: estado local (`useState<ChatMessage[]>`), inicializado com `[{role: "assistant", content: grok_dossier}]`
- Cada mensagem do usuario chama `POST /api/v1/recommend/chat` com o historico + contexto das 3 raquetes
- Chat limitado ao contexto das 3 raquetes do resultado (contexto injetado no system prompt via `ChatRequest.context`)

### Claude's Discretion
- Animacao de transicao wizard → resultado (fade, slide, ou sem animacao)
- Estilo visual do input de chat (placeholder text, icone de envio)
- Exact skeleton loading design
- Tratamento de erros de rede no frontend (toast ou mensagem inline)

### Deferred Ideas (OUT OF SCOPE)
- Knowledge base RAG (ai_knowledge_base com pgvector)
- Historico de recomendacoes por usuario (requer auth)
- Comparacao lado a lado de raquetes selecionadas pelo usuario
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REC-01 | Assistente de IA recebe perfil do jogador (nivel de jogo, estilo, orcamento) e retorna raquetes recomendadas do catalogo | `RecommendationEngine.get_recommendations()` ja implementado; endpoint `/recommend` e o wrapper HTTP que falta. Schema `RecommendationRequest` ja define todos os campos. |
| REC-02 | Cada recomendacao inclui justificativa tecnica e link de compra no Brasil | Schema `PaddleRecommendation` precisa de `market_offers: list[MarketOfferOut]`. `AffiliateService.transform_url()` ja existe. `selectinload` padrao ja funciona no catalog. |
| REC-03 | Assistente consulta catalogo em tempo real (nao depende de dados estaticos) | Engine ja usa `MarketOffer.is_active` filtrando ao vivo. Nenhuma mudanca necessaria no engine — REC-03 ja e atendido pela query existente. |
</phase_requirements>

---

## Summary

Esta fase e predominantemente de **wiring** — conectar servicos existentes a endpoints HTTP novos e construir a UI que os consome. O `RecommendationEngine`, o `LLMService` (Groq Llama 3.3-70b), e o `AffiliateService` estao completamente implementados. O gap principal e: (1) o endpoint `/recommend` nao existe em `app/api/endpoints/`, apenas o router `/recommendations` legado que os testes antigos referenciam; (2) o schema `PaddleRecommendation` nao carrega `market_offers`; (3) toda a UI da pagina `/recommend` precisa ser criada do zero.

O padrao de implementacao ja esta estabelecido pelo `catalog.py`: router com `APIRouter`, `@limiter.limit`, `Depends(get_session)`, `selectinload` em cadeia para `market_offers → store`. O endpoint `/recommend` replica esse padrao adicionando a camada de LLM. O frontend segue o padrao da Phase 14: Next.js App Router, `'use client'` com `useState`, Tailwind dark mode tokens definidos em `tailwind.config.js`.

**Atencao critica:** Os testes existentes em `test_api_recommendations.py` chamam `/api/v1/recommendations` (plural) — o endpoint que sera criado nesta fase usa o prefixo `/recommend`. Os testes existentes precisam ser atualizados ou novos testes criados para o novo path. O `grok_dossier` no no-match path requer que o endpoint invoque `generate_dossier()` com lista vazia quando `len(recommendations) == 0` pos-fallback.

**Recomendacao primaria:** Criar `app/api/endpoints/recommend.py` replicando o padrao de `catalog.py`, extender `PaddleRecommendation` com `market_offers`, e construir a pagina `/recommend` como componente React puro com estado local (sem lib externa de wizard).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | ja instalado | HTTP router, dependency injection | Padrao do projeto |
| SQLModel + SQLAlchemy | ja instalado | ORM async, `selectinload` | Padrao do projeto |
| slowapi | ja instalado | Rate limiting por IP | Padrao do projeto — `@limiter.limit("30/minute")` |
| groq (AsyncGroq) | ja instalado | LLM via `llm_service` singleton | Unico provider LLM do projeto |
| Next.js 14 (App Router) | ja instalado | Frontend SSR + client components | Padrao Phase 14 |
| Tailwind CSS | ja instalado | Estilizacao com design tokens customizados | Padrao Phase 14 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `selectinload` (SQLAlchemy) | ja instalado | Eager load `market_offers → store` | Necessario para evitar N+1 ao serializar ofertas |
| `AffiliateService` | interno | Transforma store URLs em links afiliados | Aplicar em toda `store_url` antes de serializar |
| `pydantic BaseModel` | ja instalado | Schemas `MarketOfferOut`, extensao de `PaddleRecommendation` | Tipagem de request/response |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Estado local (useState) para wizard | Biblioteca de form/wizard (react-hook-form + stepper) | Estado local e suficiente para 3 steps sem validacao complexa; evita dependencia nova |
| Groq Llama 3.3-70b (existente) | Outro LLM | Locked — nao explorar alternativas |

**Installation:** Nenhuma nova dependencia necessaria — todas as bibliotecas ja estao instaladas.

## Architecture Patterns

### Recommended Project Structure

```
app/
├── api/endpoints/
│   └── recommend.py          # NOVO: APIRouter prefix="/recommend"
├── schemas/
│   └── user_profile.py       # EXTENDER: adicionar MarketOfferOut, market_offers em PaddleRecommendation
└── main.py                   # EDITAR: include_router(recommend_router)

frontend/
├── app/
│   ├── catalog/
│   │   └── catalog-client.tsx  # EDITAR: adicionar CTA para /recommend
│   └── recommend/
│       └── page.tsx            # NOVO: wizard + resultado + chat
├── types/
│   └── recommend.ts            # NOVO: tipos TypeScript para a API /recommend
└── lib/
    └── api.ts                  # EDITAR se necessario: helper para /recommend
```

### Pattern 1: Endpoint /recommend replicando catalog.py

**What:** Router async com `get_session`, `selectinload` em cadeia, `@limiter.limit`
**When to use:** Toda vez que um endpoint precisa de dados eager-loaded de market_offers

```python
# Source: app/api/endpoints/catalog.py (padrao estabelecido)
from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import selectinload
from app.db.database import get_session
from app.models import PaddleMaster, MarketOffer

router = APIRouter(prefix="/recommend", tags=["recommend"])
limiter = Limiter(key_func=get_remote_address)

@router.post("")
@limiter.limit("30/minute")
async def get_recommendations(
    request: Request,
    body: RecommendationRequest,
    session: AsyncSession = Depends(get_session),
):
    engine = RecommendationEngine(session)
    result = await engine.get_recommendations(
        profile=UserProfile(**body.model_dump(exclude={"limit"})),
        limit=body.limit,
        use_ai_ranking=True,
    )
    # Enrich result com market_offers via selectinload separado ou na engine
    ...
```

### Pattern 2: selectinload para market_offers no endpoint /recommend

**What:** Carregar `market_offers` e `store` em uma segunda query apos obter os IDs recomendados
**When to use:** Quando a engine ja retornou os `PaddleRecommendation` mas sem `market_offers`

```python
# Source: app/api/endpoints/catalog.py linhas 47-49
.options(
    selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store),
)
```

O endpoint `/recommend` deve carregar os paddles finais (os 3 ranqueados) com `selectinload` em separado, ou a engine deve ser estendida para aceitar o carregamento eager. A abordagem mais simples: apos `engine.get_recommendations()` retornar os IDs, o endpoint faz uma query complementar carregando os paddles completos com `selectinload`.

### Pattern 3: Extensao do schema PaddleRecommendation

**What:** Adicionar `MarketOfferOut` e o campo `market_offers` ao schema existente
**When to use:** Sempre que a resposta de /recommend precisar de links de compra

```python
# Source: app/schemas/user_profile.py (a estender)
class MarketOfferOut(BaseModel):
    store_name: str
    price_brl: float
    store_url: str  # ja transformado por AffiliateService.transform_url()

class PaddleRecommendation(BaseModel):
    rank: int
    paddle_id: UUID
    brand_name: str
    model_name: str
    image_url: Optional[str] = None          # adicionar — necessario para os cards
    ratings: dict[str, Optional[int]]
    min_price_brl: Optional[float]
    market_offers: list[MarketOfferOut] = []  # NOVO
    match_reasons: list[str]
    tags: list[str]
    value_score: Optional[float] = None
```

### Pattern 4: No-match path no endpoint

**What:** Quando a engine retorna lista vazia, chamar `llm_service.generate_dossier()` com listas vazias
**When to use:** `len(result.recommendations) == 0`

```python
# Source: app/services/llm_service.py - generate_dossier() aceita listas vazias
if not result.recommendations:
    no_match_msg = await llm_service.generate_dossier(
        user_profile=body.model_dump(),
        top_paddles=[]
    )
    return RecommendationResult(
        ...result,
        grok_dossier=no_match_msg,
    )
```

### Pattern 5: Endpoint /recommend/chat

**What:** Wrapper HTTP sobre `llm_service.chat_with_context()`
**When to use:** Cada mensagem do usuario no painel de chat

```python
@router.post("/chat")
@limiter.limit("60/minute")
async def chat(request: Request, body: ChatRequest):
    reply = await llm_service.chat_with_context(
        chat_history=[m.model_dump() for m in body.messages],
        context=body.context,
    )
    return ChatResponse(reply=reply)
```

### Pattern 6: Wizard multi-step em React com useState puro

**What:** Componente `'use client'` com `step: 0|1|2|'result'` e campos de perfil no estado
**When to use:** UI simples sem validacao complexa — useState suficiente para 3 steps

```typescript
// Source: padrao estabelecido em frontend/app/catalog/catalog-client.tsx
'use client';
import { useState } from 'react';

type Step = 0 | 1 | 2 | 'result';
type WizardState = {
  skill_level: 'beginner' | 'intermediate' | 'advanced' | null;
  play_style: 'power' | 'control' | 'balanced' | null;
  budget_max_brl: number | null;
  has_tennis_elbow: boolean;
  weight_preference: string | null;
};
```

### Pattern 7: Chat inline com historico em estado local

**What:** `useState<ChatMessage[]>` inicializado com o `grok_dossier` como primeira mensagem
**When to use:** Apos resultado da API chegar, chat abre automaticamente

```typescript
// Estado inicial do chat apos resultado:
const [messages, setMessages] = useState<ChatMessage[]>([
  { role: 'assistant', content: result.grok_dossier ?? '' }
]);
```

### Anti-Patterns to Avoid

- **Registrar o recommend_router com prefix duplicado:** `app.include_router(recommend_router, prefix="/api/v1")` + `APIRouter(prefix="/recommend")` = `/api/v1/recommend`. Nao adicionar `/recommend` em ambos os lugares.
- **Chamar `generate_ai_recommendations()` no endpoint:** A engine ja faz isso internamente. O endpoint apenas instancia a engine e chama `get_recommendations()`.
- **N+1 de market_offers:** A engine atual nao carrega `market_offers` — o endpoint deve fazer isso com `selectinload` em uma query separada por paddle_id, ou refatorar a engine para aceitar o carregamento. A query separada e mais simples e nao quebra a engine existente.
- **Retornar erro HTTP quando nao ha matches:** O contrato e `recommendations: []` + `grok_dossier` com mensagem amigavel. Nunca HTTP 404/500 para no-match.
- **Chat sem context:** `ChatRequest.context` e obrigatorio — deve ser construido pelo frontend com os dados das 3 raquetes (nomes, specs, store_urls) antes de cada chamada.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rate limiting por IP | Middleware customizado | `@limiter.limit("30/minute")` via slowapi | Ja configurado globalmente em `app.state.limiter` |
| Transformacao de URL afiliada | Logica inline no endpoint | `AffiliateService.transform_url()` | Ja trata Amazon BR, ML, UTMs — edge cases de URL parsing sao complexos |
| Ranking de raquetes | Nova logica de score | `RecommendationEngine.get_recommendations()` | Engine completa com fallback, jitter, LLM ranking, cache — nao recriar |
| Geracao do dossier LLM | Chamada direta ao Groq | `llm_service.generate_ai_recommendations()` e `generate_dossier()` | System prompts ja afinados, tratamento de erro, fallback sem API key |
| Carregamento eager de relations | JOINs manuais | `selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store)` | Padrao SQLAlchemy async — evita N+1 e lazy load errors |

**Key insight:** O valor desta fase e a composicao — os servicos existentes ja resolvem os problemas dificeis (ranking com LLM, afiliados, eager loading). O endpoint e a UI sao a camada de entrega.

## Common Pitfalls

### Pitfall 1: Testes existentes apontam para /api/v1/recommendations (path legado)
**What goes wrong:** `test_api_recommendations.py` chama `/api/v1/recommendations` — se o novo endpoint usar `/api/v1/recommend` sem um alias, os testes existentes vao falhar ou passar fantasmas.
**Why it happens:** O endpoint legado provavelmente existia em um router diferente (`/recommendations`). O novo padrao usa `/recommend`.
**How to avoid:** Verificar se existe algum router com `prefix="/recommendations"` que ja inclui o endpoint. Se nao existir (apenas nos testes), criar o novo endpoint em `/recommend` e atualizar os testes para apontar ao novo path.
**Warning signs:** 404 nos testes existentes apos o merge.

### Pitfall 2: market_offers nao carregados pela engine atual
**What goes wrong:** `RecommendationEngine.get_recommendations()` usa `outerjoin` na subquery de precos mas nao usa `selectinload` — logo `paddle.market_offers` nao e carregado.
**Why it happens:** A engine foi construida antes de o endpoint precisar de `market_offers` na resposta.
**How to avoid:** O endpoint `/recommend` deve fazer uma segunda query com `selectinload` nos 3 paddles do resultado, ou adicionar `.options(selectinload(...))` ao query principal da engine. A segunda query separada nao quebra a engine existente.
**Warning signs:** `MissingGreenlet` / lazy load error em producao ao acessar `paddle.market_offers`.

### Pitfall 3: image_url ausente no schema PaddleRecommendation
**What goes wrong:** Os cards da UI precisam exibir imagem da raquete, mas `PaddleRecommendation` atual nao tem `image_url`.
**Why it happens:** O schema foi criado antes da UI existir.
**How to avoid:** Adicionar `image_url: Optional[str] = None` ao schema ao mesmo tempo que `market_offers`.
**Warning signs:** Cards sem imagem na UI mesmo quando `PaddleMaster.image_url` tem valor.

### Pitfall 4: Contexto do chat mal formatado
**What goes wrong:** `ChatRequest.context` chega vazio ou sem informacao util, e o LLM da respostas genericas.
**Why it happens:** Frontend monta a string de contexto sem incluir specs e store_urls.
**How to avoid:** Definir um formato de contexto canonico no frontend que inclua: nome, brand, specs relevantes, lista de lojas com URL. O `chat_with_context()` injeta esse contexto no system prompt — qualidade do contexto determina qualidade das respostas.
**Warning signs:** LLM inventando lojas ou specs que nao existem (alucinacao por falta de contexto).

### Pitfall 5: Rate limit muito restritivo quebrando UX
**What goes wrong:** `"30/minute"` no `/recommend` pode bloquear usuarios legítimos em sessoes de teste intenso (ex: refazer o quiz varias vezes).
**Why it happens:** LLM calls sao caras — o limite e conservador.
**How to avoid:** O limite e uma decisao locked (30/min). Garantir que o frontend exiba mensagem clara quando receber HTTP 429 (nao apenas erro generico).
**Warning signs:** Usuarios vendo tela de erro sem explicacao.

### Pitfall 6: No-match com lista vazia causa excecao no dossier
**What goes wrong:** `generate_dossier(user_profile, top_paddles=[])` pode gerar dossier confuso sem raquetes para comentar.
**Why it happens:** O system prompt do `generate_dossier()` espera que haja raquetes na lista.
**How to avoid:** Para o no-match, usar `generate_dossier()` com uma instrucao customizada no `user_prompt` indicando que nao ha resultados — ou usar um template fixo sem LLM para o caso de lista vazia (mais previsivel). O CONTEXT.md diz para usar `generate_dossier()` — seguir essa decisao mas verificar que o prompt gerado faz sentido com lista vazia.
**Warning signs:** Dossier de no-match mencionando raquetes que nao existem.

## Code Examples

### Endpoint /recommend — estrutura minima

```python
# Source: replica de app/api/endpoints/catalog.py com adaptacoes
from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.database import get_session
from app.models import PaddleMaster, MarketOffer
from app.schemas.user_profile import (
    RecommendationRequest, RecommendationResult,
    UserProfile, PaddleRecommendation, MarketOfferOut
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.recommendation_engine import RecommendationEngine
from app.services.llm_service import llm_service
from app.services.affiliate_service import get_affiliate_service

router = APIRouter(prefix="/recommend", tags=["recommend"])
limiter = Limiter(key_func=get_remote_address)

@router.post("", response_model=RecommendationResult)
@limiter.limit("30/minute")
async def post_recommendations(
    request: Request,
    body: RecommendationRequest,
    session: AsyncSession = Depends(get_session),
):
    ...

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("60/minute")
async def post_chat(
    request: Request,
    body: ChatRequest,
):
    ...
```

### Registro em main.py

```python
# Source: app/main.py linhas 19-20 e 153-155 (padrao exato)
from app.api.endpoints.recommend import router as recommend_router
# ...
app.include_router(recommend_router, prefix="/api/v1")
```

### selectinload para enriquecer as 3 raquetes do resultado

```python
# Source: padrao de catalog.py linhas 47-49
from sqlmodel import select
from sqlalchemy.orm import selectinload

async def _load_paddles_with_offers(
    session: AsyncSession,
    paddle_ids: list[UUID]
) -> dict[UUID, PaddleMaster]:
    stmt = (
        select(PaddleMaster)
        .options(selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store))
        .where(PaddleMaster.id.in_(paddle_ids))
    )
    result = await session.exec(stmt)
    return {p.id: p for p in result.all()}
```

### Serializacao de market_offers com affiliate

```python
# Source: catalog.py linhas 122-133 + affiliate_service.py transform_url()
affiliate = get_affiliate_service()
market_offers = sorted(
    [
        MarketOfferOut(
            store_name=o.store.name,
            price_brl=float(o.price_brl),
            store_url=affiliate.transform_url(o.url, store_name=o.store.name),
        )
        for o in paddle.market_offers
        if o.is_active
    ],
    key=lambda x: x.price_brl,
)
```

### Frontend: tipos TypeScript para /recommend

```typescript
// Source: padrao de frontend/types/catalog.ts
// frontend/types/recommend.ts  (NOVO)

export interface MarketOffer {
  store_name: string;
  price_brl: number;
  store_url: string;
}

export interface PaddleRecommendation {
  rank: number;
  paddle_id: string;
  brand_name: string;
  model_name: string;
  image_url: string | null;
  ratings: Record<string, number | null>;
  min_price_brl: number | null;
  market_offers: MarketOffer[];
  match_reasons: string[];
  tags: string[];
  value_score: number | null;
}

export interface RecommendationResult {
  user_profile: Record<string, unknown>;
  recommendations: PaddleRecommendation[];
  filters_applied: Record<string, boolean>;
  total_matching: number;
  returned: number;
  grok_dossier: string | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  context: string;
  paddle_id?: string;
}

export interface ChatResponse {
  reply: string;
}
```

### Frontend: submit do wizard e inicializacao do chat

```typescript
// Source: padrao de frontend/app/catalog/catalog-client.tsx
const handleSubmit = async () => {
  setIsLoading(true);
  try {
    const res = await fetch(`${apiBase}/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(wizardState),
    });
    if (!res.ok) throw new Error('API error');
    const data: RecommendationResult = await res.json();
    setResult(data);
    setStep('result');
    // Chat inicializa automaticamente com o grok_dossier
    if (data.grok_dossier) {
      setMessages([{ role: 'assistant', content: data.grok_dossier }]);
    }
  } catch (err) {
    setNetworkError('Tente novamente em instantes.');
  } finally {
    setIsLoading(false);
  }
};
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Endpoint `/recommendations` (plural, legado nos testes) | Novo endpoint `/recommend` (singular, padrao REST) | Phase 15 | Testes existentes precisam ser atualizados |
| `PaddleRecommendation` sem `market_offers` | Schema estendido com `market_offers: list[MarketOfferOut]` | Phase 15 | REC-02 atendido |
| Sem UI de recomendacao | Pagina `/recommend` com wizard + cards + chat | Phase 15 | REC-01 entregavel |

**Deprecated/outdated:**
- Tests em `test_api_recommendations.py` que chamam `/api/v1/recommendations`: devem ser atualizados para `/api/v1/recommend` ou o endpoint legado deve ser mantido como alias (nao recomendado — complexidade desnecessaria).

## Open Questions

1. **Router legado `/recommendations` (plural)**
   - What we know: `test_api_recommendations.py` testa `POST /api/v1/recommendations`. Nenhum arquivo `app/api/endpoints/recommendations.py` foi encontrado no codigo atual — o router legado pode nao existir mais.
   - What's unclear: Se o endpoint `/recommendations` (plural) esta registrado em algum lugar nao explorado (ex: `app/api/routes.py`).
   - Recommendation: Antes de implementar, verificar `app/api/routes.py` para ver se ja existe o router plural. Se existir, o novo endpoint deve subsitui-lo ou ser um alias. Se nao existir, atualizar os testes para o novo path `/recommend`.

2. **market_offers carregamento na engine vs. no endpoint**
   - What we know: A engine nao usa `selectinload` atualmente. Fazer isso na engine exigiria alterar `get_recommendations()`. Fazer no endpoint e mais seguro (nao quebra testes existentes da engine).
   - What's unclear: Se o planner vai preferir modificar a engine ou manter a query separada no endpoint.
   - Recommendation: Query separada no endpoint (`_load_paddles_with_offers` helper). Mantem a engine testavel de forma independente.

3. **image_url no schema**
   - What we know: `PaddleMaster.image_url` existe no modelo. O schema atual `PaddleRecommendation` nao tem `image_url`. Os cards da UI precisam.
   - What's unclear: Nao ha ambiguidade — deve ser adicionado.
   - Recommendation: Adicionar `image_url: Optional[str] = None` ao `PaddleRecommendation` junto com `market_offers`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `pytest.ini` ou `pyproject.toml` (verificar raiz do projeto) |
| Quick run command | `python3 -m pytest tests/test_api_recommendations.py tests/test_recommendation_engine.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REC-01 | POST /api/v1/recommend retorna recommendations com profile valido | integration | `python3 -m pytest tests/test_api_recommendations.py::test_recommendations_valid_request -x` | Parcial — testa path legado `/recommendations`, precisa atualizar para `/recommend` |
| REC-01 | No-match: retorna `recommendations: []` + `grok_dossier` nao vazio | integration | `python3 -m pytest tests/test_api_recommendations.py::test_recommendations_no_match -x` | ❌ Wave 0 — novo teste |
| REC-02 | Cada recomendacao contem `market_offers` com `store_url` afiliado | integration | `python3 -m pytest tests/test_api_recommendations.py::test_recommendations_market_offers -x` | ❌ Wave 0 — novo teste |
| REC-03 | Engine consulta `MarketOffer.is_active` ao vivo (sem dados estaticos) | unit | `python3 -m pytest tests/test_recommendation_engine.py -x` | Parcial — testa engine mas nao o endpoint |
| REC-01 | POST /api/v1/recommend/chat retorna `reply` nao vazio | integration | `python3 -m pytest tests/test_api_recommendations.py::test_chat_endpoint -x` | ❌ Wave 0 — novo teste |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_api_recommendations.py tests/test_recommendation_engine.py -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -x -q`
- **Phase gate:** Full suite green antes do `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_api_recommendations.py` — atualizar paths de `/recommendations` para `/recommend` e adicionar:
  - `test_recommendations_no_match` — cobre REC-01 criterio 4
  - `test_recommendations_market_offers` — cobre REC-02 (verifica `market_offers` com `store_url`)
  - `test_chat_endpoint` — cobre endpoint `/recommend/chat`
- [ ] `MockPaddle` em `tests/conftest.py` — adicionar `market_offers: list` e `image_url` para os novos testes

## Sources

### Primary (HIGH confidence)
- Codigo fonte lido diretamente: `app/services/recommendation_engine.py`, `app/services/llm_service.py`, `app/services/affiliate_service.py`, `app/schemas/user_profile.py`, `app/schemas/chat.py`, `app/api/endpoints/catalog.py`, `app/main.py`, `app/models/enums.py`
- Codigo fonte lido diretamente: `frontend/app/catalog/page.tsx`, `frontend/types/catalog.ts`, `frontend/tailwind.config.js`
- Testes lidos diretamente: `tests/test_api_recommendations.py`, `tests/test_recommendation_engine.py`, `tests/conftest.py`
- `.planning/phases/15-ai-recommendation-assistant/15-CONTEXT.md` — decisoes locked

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` — REC-01, REC-02, REC-03 definicoes oficiais
- `.planning/STATE.md` — historico de decisoes acumuladas

### Tertiary (LOW confidence)
- Nenhum item nesta categoria.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — codigo existente lido diretamente
- Architecture patterns: HIGH — baseados em codigo ja funcionando no projeto
- Pitfalls: HIGH — identificados a partir de gaps concretos entre engine existente e requisitos novos
- Validation architecture: MEDIUM — testes existentes lidos; novos testes inferidos dos requisitos

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (stack estavel, sem dependencias externas novas)
