# Phase 13: Catalog API - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

REST API endpoints that let users and the Phase 15 AI assistant query the full Brazilian paddle catalog — filtering by specs (core thickness, surface material), brand, store, and price — with each result including the store purchase URL. Creating or modifying paddle data is out of scope.

</domain>

<decisions>
## Implementation Decisions

### Route structure
- New file: `app/api/endpoints/catalog.py` with its own `APIRouter` — keeps catalog concerns separate from the existing general-purpose routes.py
- Register in `app/main.py` alongside existing routers (same pattern as `alerts_router`)
- Full paths: `GET /api/v1/catalog/paddles` and `GET /api/v1/catalog/stores`

### Spec filters (core_thickness, surface_material)
- Format: **numbers only** — `?core_thickness=16` (not "16mm"); avoids string parsing, enables numeric DB comparison
- **Multi-value support**: `?core_thickness=13&core_thickness=16` returns paddles matching EITHER value (OR logic)
- Exact match strategy — Claude decides whether to use exact `==` or SQL `IN()` clause; no fuzzy/range logic
- `surface_material`: same multi-value exact match approach; Claude decides based on stored enum values in `FaceMaterial`

### Store filter on /catalog/paddles
- Identified by **slug** (e.g., `?store=propadel`)
- **Note for planner:** `Store` model currently has no `slug` field — needs a migration to add a `slug` column (derived from `name`, URL-safe lowercase). Filter should JOIN `MarketOffer → Store` and match on `Store.slug`

### GET /catalog/stores response
- Returns per store: `id`, `name`, `slug`, `base_url`, `is_active`, `available_brands`
- Lean response — no paddle count
- Brand filter: `?brand=Joola` (string match against `available_brands` ARRAY field)

### Pagination on /catalog/paddles
- Yes — `limit` and `offset` params, consistent with existing `/paddles` endpoint
- Default: `limit=50`, max: `limit=100`
- Response envelope: `{"data": [...], "total": N, "limit": 20, "offset": 0}`

### Per-paddle response fields
- `id`, `brand` (name string), `model_name`, `specs: {core_thickness_mm, surface_material}`, `market_offers: [{store_name, price_brl, store_url}]`
- **All offers included** (not just cheapest) — user explicitly chose this so callers can see all purchase options
- Default sort: Claude decides (price ascending by cheapest offer is natural for a shopping catalog)

### Established patterns to follow
- Endpoints are public — no authentication (established in Phase 9)
- Rate limiting: `@limiter.limit("100/minute")` with slowapi (established)
- TTLCache for list endpoints if needed (established in routes.py)
- All existing patterns from `app/api/routes.py` apply

### Claude's Discretion
- Exact SQL strategy for multi-value spec filters (`IN()` or multiple `.where()` conditions)
- Default sort direction (price ascending recommended)
- Whether to add TTLCache to catalog endpoints
- How to handle paddles with no market offers (include with empty `market_offers: []` or exclude — recommend exclude since CAT-06 requires a store URL)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §"Catalog — API de Catálogo" — CAT-01 through CAT-06 acceptance criteria
- `.planning/REQUIREMENTS.md` §"Store — Catálogo de Lojas" — STORE-03 (this phase closes it)

### Existing API patterns
- `app/api/routes.py` — Existing endpoint patterns: `list_paddles`, `list_brands`, rate limiting, TTLCache, response shape `{"data": [...], "total": N}`
- `app/main.py` — Where to register the new catalog router (follow `alerts_router` pattern)
- `app/api/dependencies.py` — `get_session` dependency

### Data models
- `app/models/store.py` — `Store` model (name, base_url, is_active, available_brands); **no slug field yet — migration needed**
- `app/models/__init__.py` — Model imports (Store already exported)
- `app/models/market_offer.py` — `MarketOffer` with store FK (from Phase 11)
- `app/models/paddle.py` — `PaddleMaster`, `PaddleRead.from_paddle()` helper

### Prior phase context
- `.planning/phases/11-seed-cleanup-store-catalog/11-CONTEXT.md` — Store catalog foundation, store↔MarketOffer FK wiring
- `.planning/phases/12-spec-enrichment-scrapers/12-CONTEXT.md` — Spec enrichment: what fields are populated after Phase 12

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Store` model (`app/models/store.py`): has `name`, `base_url`, `is_active`, `available_brands` — use directly; add `slug` via migration
- `MarketOffer` model: has `store_id` FK (Phase 11), `price_brl`, `url`, `is_active` fields
- `PaddleMaster` + `PaddleRead.from_paddle()`: existing paddle response builder — catalog endpoint can use the same model but with a leaner response schema
- `get_session` dependency (`app/api/dependencies.py`): async SQLModel session, use as-is
- `limiter` + TTLCache pattern in `routes.py`: copy for catalog router

### Established Patterns
- All list endpoints use `{"data": [...], "total": N}` envelope — follow for consistency
- `selectinload()` for eager loading relations (used in `list_paddles` for brand)
- Subquery for aggregation (used in `list_paddles` for min_price/offer_count) — adapt for catalog
- `APIRouter()` with `include_router()` in `main.py` — follow for catalog router

### Integration Points
- `app/main.py`: add `from app.api.endpoints.catalog import router as catalog_router` and `app.include_router(catalog_router, prefix="/api/v1")`
- Alembic migrations: add `slug` column to `stores` table (derive from `name`, lowercase + underscores)
- `FaceMaterial` enum (`app/models/enums.py`): surface_material filter values must match this enum

</code_context>

<specifics>
## Specific Ideas

- User confirmed: return **all market offers** per paddle (not just cheapest) so callers see every Brazilian purchase option
- Response shape preview confirmed by user:
  ```json
  {
    "id": "uuid",
    "brand": "Joola",
    "model_name": "Hyperion CFS",
    "specs": {"core_thickness_mm": 16, "surface_material": "carbon_fiber"},
    "market_offers": [{"store_name": "ProPadel", "price_brl": 899.90, "store_url": "https://..."}]
  }
  ```
- Pagination response envelope confirmed by user: `{"data": [...], "total": 34, "limit": 20, "offset": 0}`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 13-catalog-api*
*Context gathered: 2026-03-21*
