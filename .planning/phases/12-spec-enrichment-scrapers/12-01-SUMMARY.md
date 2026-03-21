---
phase: 12-spec-enrichment-scrapers
plan: "01"
subsystem: infra
tags: [sqlmodel, alembic, scraper, postgres]

# Dependency graph
requires: []
provides:
  - PaddleMaster.weight_grams column with Alembic migration
  - Direct DB persistence for spec enricher via update_paddle_specs()
  - 4-field quality gate (core_thickness_mm, face_material, weight_grams, shape)
  - Test suite for all extractors and update_paddle_specs gate
  - --store CLI argument for per-store enrichment
  - Archived enrichment.py service
affects: [12-spec-enrichment-scrapers]

# Tech tracking
tech-stack:
  added: [alembic migration, sqlmodel Session, requests]
  patterns: [DB persistence layer, 4-field quality gate, store routing by slug]

key-files:
  created:
    - alembic/versions/f1a2b3c4d5e6_add_weight_grams.py
    - tests/test_spec_enricher.py
    - app/services/_archived/enrichment.py
  modified:
    - app/models/paddle.py
    - scripts/scrape_product_specs.py
    - scripts/enrich_paddles.py

key-decisions:
  - "Used update_paddle_specs() with Brand.model_name lookup (not paddle_id) to decouple scraper from DB IDs"
  - "Enrichment service archived to _archived/ rather than deleted — preserves rollback capability"

patterns-established:
  - "4-field gate: update_paddle_specs only writes when all 4 spec fields are present"
  - "Store routing: slug-based dispatch with STORE_SLUG_TO_ID mapping"

requirements-completed: [SCRP-03, SCRP-04, SCRP-05, SCRP-06]

# Metrics
duration: 12min
completed: 2026-03-21
---

# Phase 12, Plan 01: PaddleMaster weight_grams column, DB-persisting enricher with 4-field quality gate, and test suite

**DB-persisting spec enricher with 4-field quality gate: weight_grams column added to PaddleMaster, scrape_product_specs.py refactored from JSON output to direct SQLModel Session persistence, --store CLI for per-store routing, enrichment.py archived to _archived/.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-21T04:00:00Z
- **Completed:** 2026-03-21T04:12:00Z
- **Tasks:** 2
- **Files created:** 3
- **Files modified:** 3

## Accomplishments
- Added `weight_grams: Optional[float] = None` to PaddleMasterBase physical spec fields
- Created Alembic migration `f1a2b3c4d5e6_add_weight_grams` (down_revision: e27028b78fab)
- Refactored `scrape_product_specs.py`: removed JSON output, added `--store` CLI arg, added `update_paddle_specs()` with 4-field gate
- Renamed `weight_g` dict key to `weight_grams` in joola scraper and `parse_freetext_specs`
- Archived `enrichment.py` to `app/services/_archived/` — `scripts/enrich_paddles.py` updated to import from archived
- Created comprehensive test suite (27 tests passing)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add weight_grams to PaddleMaster + migration + test suite scaffold** — `01b09a7` (feat)
2. **Task 2: Refactor scrape_product_specs.py for direct DB persistence + 4-field gate + --store CLI + archive enrichment.py** — `5c3de84` (feat)

**Plan metadata:** `926207d` (docs: create phase plan)

## Files Created/Modified

- `app/models/paddle.py` — Added weight_grams: Optional[float] to PaddleMasterBase
- `alembic/versions/f1a2b3c4d5e6_add_weight_grams.py` — Migration adding weight_grams column
- `tests/test_spec_enricher.py` — 27 tests: extract_mm, extract_weight_g, map_face_material, map_shape, parse_freetext_specs, weight_grams field, 4-field gate, validation source recording
- `scripts/scrape_product_specs.py` — Removed JSON output, added update_paddle_specs(), --store arg, STORE_SLUG_TO_ID, DB persistence in main()
- `app/services/_archived/enrichment.py` — Archived from app/services/
- `scripts/enrich_paddles.py` — Updated import to use _archived path

## Decisions Made

- Used `update_paddle_specs()` with `Brand.name` + `PaddleMaster.model_name` lookup (not paddle_id) — decouples scraper from internal DB IDs
- `enrichment.py` archived to `_archived/` rather than deleted — enables rollback if US dump enrichment is needed again
- Store slug to ID mapping (`STORE_SLUG_TO_ID`) as module-level constant — extensible as more stores are added in plan 12-02

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- SQLModel/Pydantic `hasattr()` doesn't detect `weight_grams` field reliably — used `model_fields` dict check instead (same semantic, SQLModel-compatible)
- Pre-existing e2e test failure (`httpx.ConnectError`) unrelated to these changes — full unit/integration suite passes (227 tests)

## Next Phase Readiness

- Plan 12-02 (8 store extractors) can proceed — the core enricher, DB model, and 4-field gate are in place
- Plan 12-03 (GHA workflow) can proceed independently — `scrape_product_specs.py --store` interface is working

---
*Phase: 12-spec-enrichment-scrapers*
*Completed: 2026-03-21*
