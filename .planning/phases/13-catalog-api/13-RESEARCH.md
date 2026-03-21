# Phase 13: Catalog API - Research

**Researched:** 2026-03-21
**Domain:** FastAPI + SQLModel + async SQLAlchemy + Alembic + Supabase (PostgreSQL)
**Confidence:** HIGH

## Summary

Phase 13 adds two read-only catalog endpoints (`GET /api/v1/catalog/paddles` and `GET /api/v1/catalog/stores`) on top of the existing FastAPI async stack. All patterns are established in `app/api/routes.py` — the catalog router is a clean copy-and-extend exercise with one schema addition (Alembic migration to add `slug` column to `stores`) and one new `APIRouter` file.

The project has migrated to Supabase (PostgreSQL hosted at `db.dblvebhdprbtfbziypaw.supabase.co`). The existing async SQLAlchemy setup (`asyncpg` driver) and Alembic `env.py` already handle the Supabase connection correctly: `env.py` reads `DATABASE_URL_SYNC` from the environment and overrides the `.ini` URL, so **no changes to `alembic/env.py` or `app/config.py` are needed**. The `app/config.py` validator already rewrites `postgresql://` to `postgresql+asyncpg://` and translates `sslmode=` to `ssl=` for asyncpg compatibility.

One latent bug discovered during research: `app/api/routes.py` references `o.store_name` on `MarketOffer` objects, but Phase 11's Alembic migration (`e27028b78fab`) dropped that column and replaced it with a `store_id` FK. The catalog endpoint must NOT replicate this pattern — it must JOIN `MarketOffer -> Store` via the ORM relationship and read `offer.store.name` directly.

**Primary recommendation:** Create `app/api/endpoints/catalog.py` with two routes; write one Alembic migration for `stores.slug`; use `selectinload(MarketOffer.store)` to fetch store name — never `o.store_name`.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- New file: `app/api/endpoints/catalog.py` with its own `APIRouter`
- Register in `app/main.py` alongside existing routers (same pattern as `alerts_router`)
- Full paths: `GET /api/v1/catalog/paddles` and `GET /api/v1/catalog/stores`
- Spec filter format: numbers only — `?core_thickness=16` (not "16mm")
- Multi-value spec filters: `?core_thickness=13&core_thickness=16` — OR logic (SQL `IN`)
- Exact match strategy for spec filters (no fuzzy/range logic)
- `surface_material`: same multi-value exact match approach; values match `FaceMaterial` enum
- Store filter on `/catalog/paddles`: by slug — `?store=propadel`
- `Store` model currently has NO `slug` field — migration required (lowercase + hyphens from `name`)
- `/catalog/stores` response fields: `id`, `name`, `slug`, `base_url`, `is_active`, `available_brands`
- Brand filter on `/catalog/stores`: `?brand=Joola` — string match against `available_brands` ARRAY field
- Pagination on `/catalog/paddles`: `limit` (default 50, max 100) and `offset` params
- Response envelope: `{"data": [...], "total": N, "limit": 20, "offset": 0}`
- Per-paddle response: `id`, `brand` (name string), `model_name`, `specs: {core_thickness_mm, surface_material}`, `market_offers: [{store_name, price_brl, store_url}]`
- All offers included per paddle (not just cheapest)
- Endpoints are public — no authentication
- Rate limiting: `@limiter.limit("100/minute")` with slowapi

### Claude's Discretion
- Exact SQL strategy for multi-value spec filters (`IN()` — preferred over multiple `.where()`)
- Default sort direction (price ascending by cheapest offer recommended)
- Whether to add TTLCache to catalog endpoints
- Paddles with no active market offers: **exclude** (CAT-06 requires a store URL; empty `market_offers` would violate this)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STORE-03 | API returns list of stores with metadata and filter by available brand | `GET /api/v1/catalog/stores` with `?brand=` filter on `available_brands` ARRAY; `Store` model has all fields except `slug` (migration needed) |
| CAT-01 | User can list all paddles available in Brazil via API endpoint | `GET /api/v1/catalog/paddles` with INNER JOIN on active offers ensures only paddles with live offers appear |
| CAT-02 | User can filter paddles by core thickness | `?core_thickness=16` maps to spec field `core_thickness_mm IN (16)` — multi-value `List[int]` query param |
| CAT-03 | User can filter paddles by surface material | `?surface_material=carbon` maps to `FaceMaterial` enum values; `IN()` clause on face_material field |
| CAT-04 | User can filter paddles by price range (BRL) | `?price_min=500&price_max=1500` — filter on subquery `min(MarketOffer.price_brl)` per paddle |
| CAT-05 | User can filter paddles by brand and by store | `?brand=Joola` on `Brand.name`; `?store=propadel` on new `Store.slug` via JOIN |
| CAT-06 | Each paddle returned includes Brazilian store purchase URL | Exclude paddles with no active `MarketOffer`; return `market_offers[].store_url` from `MarketOffer.url` |
</phase_requirements>

---

## Standard Stack

### Core (already installed — no new packages needed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | installed | HTTP framework, `APIRouter`, `Query` | Established project stack |
| sqlmodel | installed | ORM + Pydantic models | Established project stack |
| sqlalchemy[asyncio] | installed | Async engine, `selectinload`, subqueries | Established project stack |
| asyncpg | installed | Async PostgreSQL driver | Required for async SQLAlchemy + Supabase |
| alembic | installed | Schema migrations | Established for all prior migrations |
| slowapi | installed | Rate limiting `@limiter.limit()` | Established in `routes.py` |
| cachetools | installed | `TTLCache` for list endpoints | Established in `routes.py` |
| psycopg2-binary | installed | Sync driver for Alembic migrations | Used via `DATABASE_URL_SYNC` |

**No new packages required for this phase.**

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `selectinload` for offers | `joinedload` | `selectinload` avoids Cartesian product; preferred for one-to-many |
| Alembic migration for slug | `_sync_missing_columns` auto-sync | Alembic is correct; `_sync_missing_columns` cannot handle computed values or indexes |

---

## Architecture Patterns

### Recommended File Structure
```
app/
├── api/
│   ├── endpoints/
│   │   ├── alerts.py          # existing
│   │   ├── history.py         # existing
│   │   ├── quality.py         # existing
│   │   └── catalog.py         # NEW — Phase 13
│   └── routes.py              # existing (do not modify)
alembic/
└── versions/
    └── XXXXXX_add_slug_to_stores.py  # NEW — Phase 13
```

### Pattern 1: APIRouter registration (follow alerts_router)
**What:** Create a standalone router, import in `main.py`, register with `/api/v1` prefix.

```python
# app/api/endpoints/catalog.py
from fastapi import APIRouter
router = APIRouter(prefix="/catalog", tags=["catalog"])

# app/main.py (add after alerts_router line)
from app.api.endpoints.catalog import router as catalog_router
app.include_router(catalog_router, prefix="/api/v1")
```

### Pattern 2: Session dependency
**What:** Import `get_session` from `app.db.database`, not from `app.api.dependencies` (which only has `get_rate_limiter`).

```python
from app.db.database import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends

@router.get("/paddles")
async def list_catalog_paddles(session: AsyncSession = Depends(get_session)):
    ...
```

### Pattern 3: Subquery + selectinload for catalog paddles
**What:** Subquery aggregates `min(price_brl)` per paddle (for price filter and default sort); `selectinload` fetches full offer list + store name in a second query.

```python
# Source: adapted from app/api/routes.py list_paddles()
from sqlalchemy.orm import selectinload
from sqlmodel import select, func

offer_subq = (
    select(
        MarketOffer.paddle_id,
        func.min(MarketOffer.price_brl).label("min_price"),
    )
    .where(MarketOffer.is_active.is_(True))
    .group_by(MarketOffer.paddle_id)
    .subquery()
)

query = (
    select(PaddleMaster, offer_subq.c.min_price)
    .options(
        selectinload(PaddleMaster.brand),
        selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store),
    )
    .join(offer_subq, PaddleMaster.id == offer_subq.c.paddle_id)  # INNER JOIN = exclude paddles with no offers
    .order_by(offer_subq.c.min_price)  # default: cheapest first
)
```

### Pattern 4: Multi-value query parameter (List)
**What:** FastAPI natively supports repeated query params as `List`.

```python
from typing import List, Optional
from fastapi import Query
from app.models.enums import FaceMaterial

@router.get("/paddles")
async def list_catalog_paddles(
    core_thickness: Optional[List[int]] = Query(default=None),
    surface_material: Optional[List[FaceMaterial]] = Query(default=None),
    ...
):
    if core_thickness:
        query = query.where(col("core_thickness_mm").in_(core_thickness))
    if surface_material:
        query = query.where(col("face_material").in_([m.value for m in surface_material]))
```

### Pattern 5: Store slug Alembic migration
**What:** Add `slug` column, populate via SQL regex, add unique index.

```python
# alembic/versions/XXXXXX_add_slug_to_stores.py
def upgrade():
    op.add_column('stores', sa.Column('slug', sa.String(), nullable=True))
    op.execute("""
        UPDATE stores
        SET slug = lower(
            regexp_replace(
                regexp_replace(name, '[^a-zA-Z0-9\\s-]', '', 'g'),
                '\\s+', '-', 'g'
            )
        )
    """)
    op.alter_column('stores', 'slug', nullable=False)
    op.create_index('ix_stores_slug', 'stores', ['slug'], unique=True)

def downgrade():
    op.drop_index('ix_stores_slug', table_name='stores')
    op.drop_column('stores', 'slug')
```

### Pattern 6: PostgreSQL ARRAY filter for available_brands
**What:** `available_brands` is `ARRAY(String)` in Postgres — use SQLAlchemy `any_()`.

```python
from sqlalchemy import any_

if brand:
    query = query.where(brand == any_(Store.available_brands))
```

### Anti-Patterns to Avoid
- **`o.store_name` on MarketOffer:** This column was DROPPED in Phase 11 migration. Always read store name via `offer.store.name` after `selectinload(MarketOffer.store)`.
- **Hardcoding Supabase URL in `alembic.ini`:** The ini has the old Docker URL (`postgres_v3:5432`). `alembic/env.py` overrides with `DATABASE_URL_SYNC` env var — never change the ini.
- **Using `postgresql://` for the async engine:** `app/config.py` auto-converts, but any new engine creation must use `postgresql+asyncpg://`.
- **`outerjoin` for the offer subquery:** Use INNER JOIN to exclude paddles without active offers (CAT-06 requirement).

---

## Supabase-Specific Considerations

### Connection Architecture (CONFIRMED from .env)
| Variable | Value Pattern | Driver |
|----------|--------------|--------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:***@db.dblvebhdprbtfbziypaw.supabase.co:5432/postgres` | asyncpg (FastAPI runtime) |
| `DATABASE_URL_SYNC` | `postgresql://postgres:***@db.dblvebhdprbtfbziypaw.supabase.co:5432/postgres` | psycopg2 (Alembic migrations) |

**Port 5432** = direct Postgres connection (not PgBouncer). Prepared statements work without special configuration.

### SSL
Supabase requires SSL on its cloud connections. The `.env` `DATABASE_URL` does not include `?ssl=require` explicitly, but Supabase accepts connections without it from the connection string format used. If local Alembic migrations fail with SSL errors, add `?sslmode=require` to `DATABASE_URL_SYNC`. The `app/config.py` validator already handles the `sslmode=` to `ssl=` translation for asyncpg.

### PgBouncer (NOT applicable here)
Port 5432 is direct Postgres, not PgBouncer. No `statement_cache_size=0` or `prepare_threshold=None` needed. If the project ever switches to port 6543 (PgBouncer transaction mode), asyncpg prepared statements would need to be disabled.

### RLS (Row Level Security)
The `stores` table and `market_offers` table exist from prior phases. The API connects as the `postgres` superuser — RLS policies do not apply to superuser connections. No RLS configuration needed for this phase.

### Alembic with Supabase (CONFIRMED working)
`alembic/env.py` already reads `DATABASE_URL_SYNC` in `run_migrations_online()` and overrides the ini URL. No changes to `env.py` needed.

**Command to run migration locally:**
```bash
# Ensure DATABASE_URL_SYNC is set in .env, then:
alembic upgrade head
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-value query params | Custom string splitting | FastAPI `List[int]` via `Query(default=None)` | Native support, typed, auto-documented |
| Store name on offers | Re-add `store_name` column | `selectinload(MarketOffer.store)` + `offer.store.name` | Column was dropped in Phase 11; relationship is correct model |
| ARRAY field filtering | Raw SQL string | SQLAlchemy `any_()` | Type-safe, injection-proof |
| Slug generation | Python loop over stores | Single `UPDATE` SQL in Alembic migration | Atomic, runs once, consistent |
| Pagination total count | Second full query with all filters | Separate `select(func.count(...))` query | Established pattern in `list_paddles` |

---

## Common Pitfalls

### Pitfall 1: `o.store_name` AttributeError at runtime
**What goes wrong:** `routes.py` calls `o.store_name` on `MarketOffer` objects — this attribute does not exist after Phase 11 dropped the column. Any new endpoint that copies this pattern will raise `AttributeError` at runtime.
**Why it happens:** `routes.py` was not updated after Phase 11 migration dropped `store_name`.
**How to avoid:** Use `selectinload(MarketOffer.store)` and access `offer.store.name` in the response builder.
**Warning signs:** `AttributeError: 'MarketOffer' object has no attribute 'store_name'` in logs.

### Pitfall 2: INNER JOIN is intentional — document it
**What goes wrong:** INNER JOIN on the offer subquery excludes paddles with zero active offers. This is the DESIRED behavior (CAT-06), but reviewers may flag it as a bug.
**How to avoid:** Add an inline comment: `# INNER JOIN intentionally excludes paddles with no active offers (CAT-06)`.

### Pitfall 3: FaceMaterial enum values vs. user-supplied strings
**What goes wrong:** A user passing `?surface_material=carbon_fiber` won't match `FaceMaterial.CARBON = "carbon"`.
**Actual enum values:** `"carbon"`, `"fiberglass"`, `"hybrid"`, `"kevlar"`.
**How to avoid:** Type the query param as `List[FaceMaterial]` — FastAPI will return 422 automatically for invalid values, and the `.value` property gives the correct string for the SQL `IN()` clause.

### Pitfall 4: `alembic.ini` has stale Docker URL
**What goes wrong:** Running `alembic` without `DATABASE_URL_SYNC` set uses the `.ini` fallback `postgresql://postgres:postgres@postgres_v3:5432/picklematch` — this will fail outside Docker.
**How to avoid:** Always ensure `DATABASE_URL_SYNC` is set in `.env` before running Alembic locally. The `env.py` override handles this when the env var is present.

### Pitfall 5: Nested selectinload chain for offers + store
**What goes wrong:** Forgetting `selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store)` means `offer.store` is `None` at serialization time.
**How to avoid:** Always chain the selectinload for the full relationship path needed by the response.

### Pitfall 6: PaddleMaster specs storage structure unknown
**What goes wrong:** The WHERE clause for `core_thickness` and `surface_material` filters depends on how specs are stored in the DB, which was not confirmed during research.
**How to avoid:** Planner must read `app/models/paddle.py` before writing the implementation tasks for CAT-02 and CAT-03.

---

## Code Examples

### Catalog paddles — full endpoint skeleton
```python
# app/api/endpoints/catalog.py
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from cachetools import TTLCache
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.database import get_session
from app.models import PaddleMaster, MarketOffer, Brand
from app.models.store import Store
from app.models.enums import FaceMaterial

router = APIRouter(prefix="/catalog", tags=["catalog"])
limiter = Limiter(key_func=get_remote_address)
_catalog_cache = TTLCache(maxsize=50, ttl=60)

@router.get("/paddles", response_model=dict)
@limiter.limit("100/minute")
async def list_catalog_paddles(
    request: Request,
    core_thickness: Optional[List[int]] = Query(default=None),
    surface_material: Optional[List[FaceMaterial]] = Query(default=None),
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    brand: Optional[str] = None,
    store: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    offer_subq = (
        select(
            MarketOffer.paddle_id,
            func.min(MarketOffer.price_brl).label("min_price"),
        )
        .where(MarketOffer.is_active.is_(True))
        .group_by(MarketOffer.paddle_id)
        .subquery()
    )

    query = (
        select(PaddleMaster, offer_subq.c.min_price)
        .options(
            selectinload(PaddleMaster.brand),
            selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store),
        )
        # INNER JOIN intentionally excludes paddles with no active offers (CAT-06)
        .join(offer_subq, PaddleMaster.id == offer_subq.c.paddle_id)
        .order_by(offer_subq.c.min_price)
    )

    # Filters — CAT-02/03 WHERE clause depends on PaddleMaster specs structure
    # (planner must confirm from app/models/paddle.py)
    if price_min is not None:
        query = query.where(offer_subq.c.min_price >= price_min)
    if price_max is not None:
        query = query.where(offer_subq.c.min_price <= price_max)
    if brand:
        query = query.join(Brand, PaddleMaster.brand_id == Brand.id).where(
            Brand.name.ilike(f"%{brand}%")
        )
    if store:
        query = (
            query
            .join(MarketOffer, PaddleMaster.id == MarketOffer.paddle_id)
            .join(Store, MarketOffer.store_id == Store.id)
            .where(Store.slug == store)
        )

    result = await session.exec(query.offset(offset).limit(limit))
    rows = result.all()

    data = []
    for row in rows:
        paddle = row[0]
        active_offers = [o for o in paddle.market_offers if o.is_active]
        data.append({
            "id": str(paddle.id),
            "brand": paddle.brand.name if paddle.brand else None,
            "model_name": paddle.model_name,
            "specs": {
                "core_thickness_mm": ...,  # from paddle.specs — planner fills after reading paddle.py
                "surface_material": ...,
            },
            "market_offers": [
                {
                    "store_name": o.store.name,  # NOT o.store_name
                    "price_brl": float(o.price_brl),
                    "store_url": o.url,
                }
                for o in sorted(active_offers, key=lambda x: x.price_brl)
            ],
        })

    # Count total (without pagination)
    count_q = select(func.count(PaddleMaster.id)).join(
        offer_subq, PaddleMaster.id == offer_subq.c.paddle_id
    )
    total_result = await session.exec(count_q)
    total = total_result.first() or 0

    return {"data": data, "total": total, "limit": limit, "offset": offset}
```

### Catalog stores endpoint
```python
from sqlalchemy import any_

@router.get("/stores", response_model=dict)
async def list_catalog_stores(
    brand: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    query = select(Store).where(Store.is_active.is_(True))
    if brand:
        query = query.where(brand == any_(Store.available_brands))
    result = await session.exec(query)
    stores = result.all()
    return {
        "data": [
            {
                "id": s.id,
                "name": s.name,
                "slug": s.slug,
                "base_url": s.base_url,
                "is_active": s.is_active,
                "available_brands": s.available_brands or [],
            }
            for s in stores
        ],
        "total": len(stores),
    }
```

---

## Open Questions

1. **PaddleMaster specs storage structure**
   - What we know: CONTEXT.md references `PaddleSpecs.core_thickness_mm` and `FaceMaterial`; `routes.py` accesses `paddle.specs.core_thickness_mm` suggesting a sub-object
   - What's unclear: Whether `specs` is a JSON column, a separate ORM-related table, or scalar columns on `PaddleMaster` — determines the WHERE clause for CAT-02/CAT-03
   - Recommendation: **Planner must read `app/models/paddle.py` before writing implementation tasks**

2. **`routes.py` latent bug (`o.store_name`)**
   - What we know: `routes.py` lines 323, 325, 326, 474, 475 reference `o.store_name` on `MarketOffer` objects; this column was dropped in Phase 11
   - What's unclear: Whether this surfaces in production (may be dormant if those code paths aren't exercised with live data)
   - Recommendation: Phase 13 must NOT fix this bug (out of scope); catalog endpoint must use `offer.store.name`; note as a separate fix needed

3. **Store slug values for 10 existing stores**
   - What we know: 10 stores exist with names like `ProPadel`, `Joola`, `YoSports` etc.
   - What's unclear: Exact `name` values in the DB — the migration regex must produce predictable slugs (e.g., `ProPadel` -> `propadel`)
   - Recommendation: Planner notes that filter `?store=propadel` must match what the migration produces; consider adding a test fixture that verifies slug generation

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio + httpx |
| Config file | Check `pyproject.toml` or `pytest.ini` in project root |
| Quick run command | `pytest tests/test_catalog_api.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Test Pattern (from conftest.py)
All existing API tests use `async_client` fixture which overrides `get_session` with `AsyncMock`. New catalog tests follow the same pattern:

```python
@pytest_asyncio.fixture
async def async_client():
    async def override_get_session():
        mock = AsyncMock()
        yield mock
    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
```

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STORE-03 | `GET /api/v1/catalog/stores` returns stores list | unit (mock session) | `pytest tests/test_catalog_api.py::test_list_stores -x` | No — Wave 0 |
| STORE-03 | `?brand=Joola` filters by available_brands | unit | `pytest tests/test_catalog_api.py::test_stores_filter_by_brand -x` | No — Wave 0 |
| CAT-01 | `GET /api/v1/catalog/paddles` returns paddles | unit (mock session) | `pytest tests/test_catalog_api.py::test_list_catalog_paddles -x` | No — Wave 0 |
| CAT-02 | `?core_thickness=16` filters correctly | unit | `pytest tests/test_catalog_api.py::test_filter_core_thickness -x` | No — Wave 0 |
| CAT-03 | `?surface_material=carbon` filters correctly | unit | `pytest tests/test_catalog_api.py::test_filter_surface_material -x` | No — Wave 0 |
| CAT-04 | `?price_min=500&price_max=1500` filters | unit | `pytest tests/test_catalog_api.py::test_filter_price_range -x` | No — Wave 0 |
| CAT-05 | `?brand=Joola` and `?store=propadel` filter | unit | `pytest tests/test_catalog_api.py::test_filter_brand_and_store -x` | No — Wave 0 |
| CAT-06 | Response includes store_url; no-offer paddles excluded | unit | `pytest tests/test_catalog_api.py::test_offers_included -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_catalog_api.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_catalog_api.py` — 8 test functions covering all requirements above
- [ ] Add `MockStore` class to `tests/conftest.py` (follows `MockPaddle` pattern; needs `id`, `name`, `slug`, `base_url`, `is_active`, `available_brands`)
- [ ] Add `MockMarketOfferWithStore` to `tests/conftest.py` — `MarketOffer` mock with `.store.name` accessible (since `store_name` column is gone)

---

## Sources

### Primary (HIGH confidence — direct file inspection)
- `app/api/routes.py` — established patterns: limiter, TTLCache, `get_session`, subquery, pagination envelope, `selectinload`
- `app/db/database.py` — async/sync engine setup, `get_session` generator
- `app/config.py` — URL rewriting: `postgresql://` to `postgresql+asyncpg://`, `sslmode=` to `ssl=`, `sync_database_url` property
- `alembic/env.py` — `DATABASE_URL_SYNC` override for Supabase; `pool.NullPool` for migrations
- `alembic.ini` — confirms stale Docker fallback URL; `env.py` override is essential
- `app/models/store.py` — `Store` model fields; confirms NO `slug` column yet
- `app/models/market_offer.py` — `store_id` FK, `store` relationship; confirms NO `store_name` column
- `alembic/versions/e27028b78fab_add_store_id_to_market_offers.py` — confirms `store_name` was dropped and `store_id` FK added in Phase 11
- `app/models/enums.py` — `FaceMaterial` values: `"carbon"`, `"fiberglass"`, `"hybrid"`, `"kevlar"`
- `tests/conftest.py` — test patterns: mock session override, `async_client` fixture shape
- `.env` — confirms `DATABASE_URL_SYNC` points to Supabase at port 5432 (direct Postgres)
- `.env.example` — confirms two-URL structure: `DATABASE_URL` (asyncpg) + `DATABASE_URL_SYNC` (psycopg2)
- `app/main.py` — router registration pattern (`alerts_router`)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified by direct file inspection; no new packages needed
- Architecture patterns: HIGH — established in `routes.py`; catalog is a clean extension
- Supabase integration: HIGH — `alembic/env.py` and `app/config.py` already handle it; confirmed by `.env` values
- Pitfalls: HIGH — `store_name` bug verified by cross-referencing Phase 11 migration and model definition
- Specs filter SQL: MEDIUM — depends on `PaddleMaster` specs structure; requires planner to read `app/models/paddle.py`

**Research date:** 2026-03-21
**Valid until:** 2026-04-20 (stable stack; Supabase connection confirmed working)
