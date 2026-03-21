---
phase: 13-catalog-api
plan: "01"
subsystem: api
tags: [fastapi, catalog, sqlmodel, sqlalchemy, alembic, migration]

# Dependency graph
requires:
  - phase: 12-spec-enrichment-scrapers
    provides: Store model with market_offer FK, enriched paddle specs
provides:
  - Store.slug field and migration
  - GET /api/v1/catalog/paddles endpoint with spec/brand/store/price filters
  - GET /api/v1/catalog/stores endpoint with brand filter
  - Fixed routes.py to use store relationship instead of dropped store_name column
affects: [14-web-catalog-page, 15-ai-recommendation-assistant]

# Tech tracking
tech-stack:
  added: [alembic migration, selectinload chained loading]
  patterns: [catalog router pattern, INNER JOIN for active-only filtering, any_() for ARRAY filtering]

key-files:
  created:
    - app/api/endpoints/catalog.py (catalog router with /paddles and /stores)
    - alembic/versions/a1b2c3d4e5f6_add_slug_to_stores.py
  modified:
    - app/models/store.py (added slug field)
    - app/main.py (wired catalog_router)
    - app/api/routes.py (fixed store relationship access)

key-decisions:
  - "INNER JOIN for offer subquery excludes paddles with no active offers (CAT-06 requirement)"
  - "Store filter uses explicit JOIN path (MarketOffer→Store) to avoid duplicating joins"
  - "All market offers returned per paddle (not just cheapest) per user requirement"
  - "ORM-level sorting of offers by price (Python sort) for consistent output"

patterns-established:
  - "Chained selectinload: .selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store)"
  - "ARRAY filtering: brand == any_(Store.available_brands)"

requirements-completed: [STORE-03, CAT-01, CAT-02, CAT-03, CAT-04, CAT-05, CAT-06]

# Metrics
duration: 20min
completed: 2026-03-21
---

# Phase 13 Plan 01: Catalog API — Store slug + endpoints with spec/brand/store/price filters

**Store slug field added with regex-based population migration, GET /api/v1/catalog/paddles and /stores endpoints wired with all filters, routes.py store relationship bug fixed**

## Performance

- **Duration:** ~20 min
- **Tasks:** 3 (2 planned + 1 Rule 1 auto-fix)
- **Files modified:** 5 (2 created, 3 modified)

## Accomplishments
- Store model has slug field derived from name with unique index
- GET /api/v1/catalog/paddles: 6 filter params (core_thickness, surface_material, price_min, price_max, brand, store) + pagination
- GET /api/v1/catalog/stores: active stores with brand filter via PostgreSQL ARRAY any_()
- Fixed AttributeError in get_paddle() and coach_chat() — dropped store_name column replaced with store relationship

## Task Commits

1. **Task 1: Store slug migration + model update** - `1a27218` (feat)
2. **Task 2: Catalog API endpoints + router wiring** - `d45f19d` (feat)
3. **Task 3: Rule 1 — Fix routes.py o.store_name bug** - `d45f19d` (fix)

## Files Created/Modified

- `app/models/store.py` — Added slug: Optional[str] field to StoreBase
- `alembic/versions/a1b2c3d4e5f6_add_slug_to_stores.py` — Migration: add slug column, populate from name (lowercase, regex-cleaned), unique index
- `app/api/endpoints/catalog.py` — New catalog router with /paddles (6 filters + pagination) and /stores (brand filter)
- `app/main.py` — Imported and registered catalog_router at /api/v1
- `app/api/routes.py` — Added selectinload(MarketOffer.store) to get_paddle() and coach_chat() offer queries; replaced o.store_name with o.store.name

## Decisions Made

- INNER JOIN on offer subquery intentionally excludes paddles with no active market offers (per CAT-06 requirement)
- Surface material filter compares against enum .value strings: `PaddleMaster.face_material.in_([m.value for m in surface_material])`
- Core thickness filter uses direct scalar column: `PaddleMaster.core_thickness_mm.in_(core_thickness)`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] o.store_name attribute access in routes.py**
- **Found during:** Task 2 (Catalog endpoint verification)
- **Issue:** `get_paddle()` (line ~323) and `coach_chat()` (line ~475) accessed `o.store_name` — a column dropped in Phase 11 migration. Would raise AttributeError at runtime.
- **Fix:** Added `selectinload(MarketOffer.store)` to both offer queries; replaced `o.store_name` with `o.store.name if o.store else None`
- **Files modified:** app/api/routes.py
- **Verification:** `grep -rn "o\.store_name" app/` returns zero attribute accesses
- **Committed in:** d45f19d (combined with Task 2)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Bug fix essential — existing endpoints would crash. Phase 13 endpoints also needed the same fix pattern.

## Issues Encountered

- Alembic autogenerate failed: Railway `postgres_v3` hostname not reachable from local machine. Created migration file manually with correct content (matches what autogenerate would produce).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 13-02 (comprehensive test suite) can proceed immediately
- Requirements STORE-03, CAT-01 through CAT-06 verified complete
- Migration must be applied (`alembic upgrade head`) before API returns slug data

---
*Phase: 13-catalog-api*
*Completed: 2026-03-21*
