# Phase 13: Catalog API - Research

**Researched:** 2026-03-21
**Domain:** FastAPI read-only catalog endpoints with SQLModel/SQLAlchemy async queries, Alembic migration for slug column
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- New file: `app/api/endpoints/catalog.py` with its own `APIRouter`
- Register in `app/main.py` alongside existing routers (same pattern as `alerts_router`)
- Full paths: `GET /api/v1/catalog/paddles` and `GET /api/v1/catalog/stores`
- Spec filter format: numbers only — `?core_thickness=16` (no "mm" suffix)
- Multi-value spec filters: `?core_thickness=13&core_thickness=16` returns OR match
- Exact match strategy (not fuzzy/range) for spec filters
- `surface_material` follows same multi-value exact match as `core_thickness`
- Store filter uses slug: `?store=propadel`
- `Store` model needs a migration to add a `slug` column (derived from `name`, URL-safe lowercase)
- Filter on store JOINs `MarketOffer → Store` and matches on `Store.slug`
- `GET /catalog/stores` returns: `id`, `name`, `slug`, `base_url`, `is_active`, `available_brands`
- Brand filter on stores: `?brand=Joola` (string match against `available_brands` ARRAY field)
- Pagination: `limit` (default 50, max 100) and `offset`
- Response envelope: `{"data": [...], "total": N, "limit": 20, "offset": 0}`
- Per-paddle response: `id`, `brand` (name string), `model_name`, `specs: {core_thickness_mm, surface_material}`, `market_offers: [{store_name, price_brl, store_url}]`
- All market offers included per paddle (not just cheapest)
- Endpoints are public — no authentication
- Rate limiting: `@limiter.limit("100/minute")` with slowapi

### Claude's Discretion

- Exact SQL strategy for multi-value spec filters (`IN()` vs. multiple `.where()` conditions)
- Default sort direction (price ascending recommended)
- Whether to add TTLCache to catalog endpoints
- How to handle paddles with no market offers (include with empty `market_offers: []` or exclude — recommend exclude since CAT-06 requires a store URL)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STORE-03 | API returns list of stores with metadata and filter by available brand | `GET /api/v1/catalog/stores` endpoint with `?brand=` filter against `available_brands` ARRAY |
| CAT-01 | User can list all paddles available in Brazil via API endpoint | `GET /api/v1/catalog/paddles` joining `PaddleMaster → MarketOffer → Store` |
| CAT-02 | User can filter paddles by core thickness (13mm, 16mm, 19mm) | `?core_thickness=16` multi-value query param; SQL `IN()` on `core_thickness_mm` |
| CAT-03 | User can filter paddles by surface material | `?surface_material=carbon` multi-value; SQL `IN()` on `face_material` enum |
| CAT-04 | User can filter paddles by price range (R$) | `?price_min=` / `?price_max=` against `min(MarketOffer.price_brl)` subquery |
| CAT-05 | User can filter paddles by brand and by store | `?brand=Joola` on `Brand.name`; `?store=propadel` on `Store.slug` (needs migration) |
| CAT-06 | Each paddle returned by API includes a Brazilian store URL | `market_offers` array always populated; exclude paddles with no active offers |
</phase_requirements>

---

## Summary

Phase 13 builds two read-only catalog endpoints on top of models and data already produced by Phases 11 and 12. The data layer is fully in place: `PaddleMaster`, `MarketOffer` (with `store_id` FK), `Store`, `Brand`, and the `FaceMaterial` enum. The only schema gap is that `Store` has no `slug` field — one Alembic migration is required before the store filter on `/catalog/paddles` can work.

The implementation pattern is a near-exact copy of `app/api/routes.py::list_paddles`: async SQLModel session, subquery for offer aggregation, `selectinload()` for relations, rate limiting via `slowapi`, and the `{"data": [...], "total": N, "limit": L, "offset": O}` envelope. The catalog router differs in response shape (leaner, store-purchase-URL-centric) and in adding spec/store/brand filters not present in the existing endpoint.

Test pattern for the project is `pytest` + `httpx.AsyncClient` with `ASGITransport` and mocked `get_session` dependency overrides. New tests for catalog endpoints should follow `tests/test_api_paddles.py` exactly.

**Primary recommendation:** Copy the `list_paddles` skeleton into `catalog.py`, add the slug migration, wire the new filters, and define a lean `CatalogPaddleRead` response schema that embeds `market_offers` with `store_url`.

---

## Standard Stack

### Core (already installed — no new packages needed)

| Library | Version in use | Purpose | Note |
|---------|---------------|---------|------|
| fastapi | project-pinned | Router, Query params, Depends | Already used |
| sqlmodel | project-pinned | Async ORM / response schemas | Already used |
| sqlalchemy | project-pinned | `select`, `func`, `selectinload`, subqueries | Already used |
| alembic | project-pinned | DB migrations (slug column) | Already used |
| slowapi | project-pinned | `@limiter.limit()` rate limiting | Already used |
| cachetools | project-pinned | `TTLCache` for list endpoints | Already used |
| pytest / httpx | project-pinned | Async API tests | Already used |

No new dependencies are needed for this phase.

### Architecture Patterns

#### Recommended File Layout

```
app/
├── api/
│   ├── endpoints/
│   │   ├── catalog.py         # NEW — catalog router (this phase)
│   │   ├── alerts.py          # existing
│   │   ├── history.py         # existing
│   │   └── quality.py         # existing
│   └── routes.py              # existing general router
├── models/
│   └── store.py               # ADD slug field + StoreRead update
alembic/
└── versions/
    └── XXXX_add_slug_to_stores.py   # NEW migration
tests/
└── test_api_catalog.py        # NEW test file
```

#### Pattern 1: New APIRouter registration in main.py

Follow the `alerts_router` pattern exactly:

```python
# app/main.py
from app.api.endpoints.catalog import router as catalog_router
app.include_router(catalog_router, prefix="/api/v1")
```

The catalog router uses `prefix="/catalog"` internally so full paths become `/api/v1/catalog/paddles` and `/api/v1/catalog/stores`.

#### Pattern 2: Catalog paddles query — subquery + JOIN

The existing `list_paddles` already demonstrates the subquery pattern for offer aggregation. For the catalog endpoint the JOIN must be **inner** (not outer) to enforce CAT-06 (only paddles with active offers):

```python
# Aggregate offers per paddle
offer_subq = (
    select(
        MarketOffer.paddle_id,
        func.min(MarketOffer.price_brl).label("min_price"),
    )
    .where(MarketOffer.is_active.is_(True))
    .group_by(MarketOffer.paddle_id)
    .subquery()
)

# INNER JOIN enforces CAT-06: only paddles with active offers
query = (
    select(PaddleMaster)
    .options(selectinload(PaddleMaster.brand))
    .options(selectinload(PaddleMaster.market_offers))
    .join(offer_subq, PaddleMaster.id == offer_subq.c.paddle_id)
)
```

For the `market_offers` list on each paddle (store_name + store_url), load the `store` relation via `selectinload(MarketOffer.store)` or fetch store data in a separate subquery. The `MarketOffer` model already has a `store: Optional["Store"]` relationship.

#### Pattern 3: Multi-value IN filter for specs

Use Python's `List[float]` / `List[str]` Query params with `IN()`:

```python
from typing import List, Optional
from fastapi import Query

async def list_catalog_paddles(
    core_thickness: Optional[List[float]] = Query(default=None),
    surface_material: Optional[List[str]] = Query(default=None),
    ...
):
    if core_thickness:
        query = query.where(PaddleMaster.core_thickness_mm.in_(core_thickness))
    if surface_material:
        # Validate against FaceMaterial enum values
        query = query.where(PaddleMaster.face_material.in_(surface_material))
```

SQLModel/SQLAlchemy `.in_()` is the correct clause — avoids multiple `.where()` conditions.

#### Pattern 4: Store slug filter with JOIN

```python
if store:
    query = (
        query
        .join(MarketOffer, PaddleMaster.id == MarketOffer.paddle_id)
        .join(Store, MarketOffer.store_id == Store.id)
        .where(Store.slug == store)
    )
```

Note: if the offer subquery already JOINs `MarketOffer`, be careful not to create a cartesian product. Consolidate joins.

#### Pattern 5: Brand filter by name string

```python
if brand:
    query = (
        query
        .join(Brand, PaddleMaster.brand_id == Brand.id)
        .where(Brand.name.ilike(brand))  # case-insensitive
    )
```

#### Pattern 6: Store list with ARRAY contains filter

```postgresql
-- ?brand=Joola → filter on available_brands ARRAY
-- SQLAlchemy: use .any() or @> operator
```

```python
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String

if brand:
    query = query.where(Store.available_brands.any(brand))
    # OR: query.where(cast([brand], ARRAY(String)).contained_by(Store.available_brands))
    # Simplest: Store.available_brands.contains([brand])  — PostgreSQL @> operator
```

The `available_brands` column is already `ARRAY(String)` — use SQLAlchemy array containment.

#### Pattern 7: Slug migration

```python
# alembic/versions/XXXX_add_slug_to_stores.py
def upgrade():
    op.add_column('stores', sa.Column('slug', sa.String(), nullable=True))
    # Populate from name: lowercase, spaces→underscores, strip special chars
    op.execute("""
        UPDATE stores
        SET slug = regexp_replace(lower(name), '[^a-z0-9]+', '_', 'g')
    """)
    op.alter_column('stores', 'slug', nullable=False)
    op.create_unique_constraint('uq_stores_slug', 'stores', ['slug'])
```

#### Pattern 8: Lean response schemas

Define new schemas in `catalog.py` (or a `app/schemas/catalog.py`) rather than reusing `PaddleRead` which carries ratings and internal fields not needed here:

```python
class CatalogOfferOut(SQLModel):
    store_name: str
    price_brl: float
    store_url: str

class CatalogPaddleOut(SQLModel):
    id: UUID
    brand: str              # brand name string (not brand_id)
    model_name: str
    specs: CatalogSpecsOut  # only core_thickness_mm + surface_material
    market_offers: List[CatalogOfferOut]

class CatalogSpecsOut(SQLModel):
    core_thickness_mm: Optional[float]
    surface_material: Optional[FaceMaterial]

class StoreOut(SQLModel):
    id: int
    name: str
    slug: str
    base_url: str
    is_active: bool
    available_brands: Optional[List[str]]
```

#### Pattern 9: Test pattern (existing project convention)

```python
# tests/test_api_catalog.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.db.database import get_session

@pytest.mark.asyncio
async def test_catalog_paddles_empty():
    """Returns empty list (not error) when no paddles match — CAT success criteria."""
    async def mock_session():
        mock = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_result.first.return_value = 0
        mock.exec.return_value = mock_result
        yield mock

    app.dependency_overrides[get_session] = mock_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/catalog/paddles?brand=DoesNotExist")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["total"] == 0
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ARRAY containment filter | Custom Python loop filter | SQLAlchemy `.any()` / `.contains()` on ARRAY column | Pushed to DB, correct for NULL handling |
| Multi-value query params | Manual string split | FastAPI `List[str]` Query type | Native FastAPI feature, handles repeated params |
| Rate limiting | Custom middleware | `@limiter.limit()` — already in project | Consistent with existing endpoints |
| Slug generation | Python function at runtime | Alembic migration with `regexp_replace()` | Slug stored in DB for index/query efficiency |
| IN() filtering | Multiple `.where(field == val)` | SQLAlchemy `.in_()` | Single SQL clause, correct semantics |

---

## Common Pitfalls

### Pitfall 1: Cartesian product from double JOIN on MarketOffer

**What goes wrong:** The offer subquery JOINs `MarketOffer` and the store slug filter also JOINs `MarketOffer` — two JOINs on the same table can multiply rows.

**How to avoid:** Add the store slug filter inside the offer subquery itself (filter `where MarketOffer.store_id = store.id AND store.slug = ?`) rather than as a separate JOIN on the main query. Or use a single CTE.

**Warning signs:** `total` count is inflated; paddles appear multiple times.

### Pitfall 2: Paddles with no market offers appearing in results

**What goes wrong:** Using `outerjoin` on the offer subquery (like the existing `list_paddles`) includes paddles with zero offers, violating CAT-06.

**How to avoid:** Use `join` (INNER JOIN) on the offer subquery for `/catalog/paddles`. Exclude paddles where `market_offers` would be empty.

### Pitfall 3: slug column missing from Store model causes runtime error

**What goes wrong:** Alembic migration added the DB column but `Store` SQLModel class still doesn't have `slug: str` — queries referencing `Store.slug` fail at runtime.

**How to avoid:** Update `Store` model and `StoreRead` schema in the same wave as the migration.

### Pitfall 4: `surface_material` filter values must match FaceMaterial enum

**What goes wrong:** User passes `?surface_material=Carbon` but stored value is `"carbon"` (lowercase enum). No match returned, silently empty.

**How to avoid:** Normalize input to lowercase before comparing, or use `.ilike()`. Document accepted values in the OpenAPI description. Values are: `carbon`, `fiberglass`, `hybrid`, `kevlar`.

### Pitfall 5: COUNT query for `total` not applying same filters as data query

**What goes wrong:** The existing `list_paddles` uses a separate count query and manually re-applies filters — easy to forget one. Total will be wrong.

**How to avoid:** Extract filter conditions into a shared helper function applied to both data query and count query.

### Pitfall 6: Rate limiter state not found on app

**What goes wrong:** `@limiter.limit("100/minute")` needs `app.state.limiter = limiter`. The main app already sets this. But if a second `Limiter` instance is created in `catalog.py` it won't be attached to app state.

**How to avoid:** Import the existing `limiter` from `routes.py` or re-use the same instance. Do NOT instantiate a new `Limiter` in `catalog.py` — import from the existing one or instantiate with `get_remote_address` and attach to app state in `main.py`.

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|-----------------|--------|
| Manual offer aggregation in Python | Subquery with `func.min()` pushed to DB | N+1 elimination, used in `list_paddles` |
| `store_name` string on `MarketOffer` | `store_id` FK → `Store` table (Phase 11) | Enables JOIN-based store filter |
| No spec fields on scrapers | Phase 12 enriched `core_thickness_mm`, `face_material` on 70%+ paddles | Filters will have data to operate on |

---

## Open Questions

1. **`limiter` import strategy**
   - What we know: `routes.py` creates `limiter = Limiter(key_func=get_remote_address)`; `main.py` attaches it as `app.state.limiter`
   - What's unclear: The cleanest import path for `catalog.py` to reuse it without circular imports
   - Recommendation: Create a new `Limiter` instance in `catalog.py` (same pattern as `routes.py` does) and add `app.state.limiter` attachment in `main.py` if needed — or factor `limiter` into `app/api/dependencies.py`

2. **`selectinload` for market_offers + store on catalog query**
   - What we know: `PaddleMaster.market_offers` relation exists; `MarketOffer.store` relation exists
   - What's unclear: Whether `selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store)` works cleanly with SQLModel's async session
   - Recommendation: Use chained `selectinload` — this is standard SQLAlchemy 2.x pattern; test with mock to verify load strategy

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (async via pytest-asyncio) |
| Config file | `pytest.ini` or `pyproject.toml` (existing) |
| Quick run command | `pytest tests/test_api_catalog.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CAT-01 | `GET /catalog/paddles` returns paddles list | unit (mocked) | `pytest tests/test_api_catalog.py::test_catalog_paddles_returns_list -x` | Wave 0 |
| CAT-02 | `?core_thickness=16` filters by thickness | unit (mocked) | `pytest tests/test_api_catalog.py::test_filter_core_thickness -x` | Wave 0 |
| CAT-03 | `?surface_material=carbon` filters by material | unit (mocked) | `pytest tests/test_api_catalog.py::test_filter_surface_material -x` | Wave 0 |
| CAT-04 | `?price_min=` / `?price_max=` filter by price | unit (mocked) | `pytest tests/test_api_catalog.py::test_filter_price_range -x` | Wave 0 |
| CAT-05 | `?brand=` and `?store=` filters work | unit (mocked) | `pytest tests/test_api_catalog.py::test_filter_brand_and_store -x` | Wave 0 |
| CAT-06 | Each paddle response includes store URL | unit (mocked) | `pytest tests/test_api_catalog.py::test_paddle_has_store_url -x` | Wave 0 |
| STORE-03 | `GET /catalog/stores` returns stores + brand filter | unit (mocked) | `pytest tests/test_api_catalog.py::test_catalog_stores -x` | Wave 0 |
| (all) | Empty list returned (not error) when no match | unit (mocked) | `pytest tests/test_api_catalog.py::test_empty_result_not_error -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_api_catalog.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_api_catalog.py` — covers all CAT + STORE-03 requirements above
- [ ] No framework gaps — pytest, httpx, AsyncMock already in project

---

## Sources

### Primary (HIGH confidence)

- Direct code inspection: `app/api/routes.py` — existing `list_paddles` pattern, limiter, TTLCache, response envelope
- Direct code inspection: `app/models/store.py` — confirmed `slug` field missing
- Direct code inspection: `app/models/market_offer.py` — confirmed `store_id` FK and `store` relationship
- Direct code inspection: `app/models/paddle.py` — `PaddleMaster`, `PaddleRead`, `PaddleSpecs` structure
- Direct code inspection: `app/models/enums.py` — `FaceMaterial` values: `carbon`, `fiberglass`, `hybrid`, `kevlar`
- Direct code inspection: `app/main.py` — `alerts_router` registration pattern
- Direct code inspection: `tests/test_api_paddles.py` — AsyncClient + ASGITransport + mock session pattern
- Direct code inspection: `alembic/versions/` — existing migration pattern confirmed

### Secondary (MEDIUM confidence)

- SQLAlchemy docs pattern: `ARRAY.any()` / `.contains()` for PostgreSQL array containment
- FastAPI docs: `List[str]` Query params for multi-value filters

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in project, verified by code inspection
- Architecture: HIGH — patterns copied directly from existing working code in routes.py
- Pitfalls: HIGH — identified from direct inspection of existing code patterns and known SQLAlchemy gotchas

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (stable stack)
