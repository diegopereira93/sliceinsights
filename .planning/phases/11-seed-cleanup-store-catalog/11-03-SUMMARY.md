---
phase: 11-seed-cleanup-store-catalog
plan: "03"
subsystem: database
tags: [pytest, cleanup, migration, store-id]

requires:
  - phase: "11-02"
    provides: "Shared ingestor module with ingest_rows()"
provides:
  - All seed CSV files and seed_brazil_catalog.py removed
  - New tests for ingestor and pipeline smoke tests
  - Updated quality_aggregator and slo_validator to use store_id
affects: [12-spec-enrichment]

tech-stack:
  added: [pytest]
  patterns: [scraper-to-db-pipeline]

key-files:
  created:
    - tests/test_ingestor.py
    - tests/test_pipeline_no_csv.py
  modified:
    - tests/test_scrapers.py
    - app/api/routes.py
    - scripts/quality_aggregator.py
    - scripts/slo_validator.py
  deleted:
    - app/data/brazil_pickleball_store.csv
    - app/data/joola_brazil.csv
    - app/data/paddle_stats_dump.csv
    - app/db/seed_brazil_catalog.py

key-decisions:
  - "Deprecated /admin/seed endpoint — seeding now done via scrapers"
  - "quality_aggregator and slo_validator use store_id via Store join"

patterns-established:
  - "Pipeline architecture: scraper -> ingest_rows -> DB (no CSV in data path)"

requirements-completed: [SCRP-01]

duration: 25min
completed: 2026-03-21
---

# Phase 11: Remove Seed CSVs and Update Tests Summary

**All seed CSV files deleted, seed_brazil_catalog.py removed, tests updated, quality_aggregator and slo_validator fixed to use store_id**

## Performance

- **Duration:** 25 min
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Deleted all seed CSV files (brazil_pickleball_store.csv, joola_brazil.csv, paddle_stats_dump.csv)
- Deleted seed_brazil_catalog.py (fully replaced by ingestor.py)
- Created test_ingestor.py with 17 unit tests covering is_paddle, normalize, ingest_rows
- Created test_pipeline_no_csv.py smoke tests confirming no CSV dependencies
- Updated test_scrapers.py to mock ingest_rows instead of save_to_csv
- Updated /admin/seed API endpoint (deprecated, returns 410 Gone)
- Updated scripts/quality_aggregator.py to use store_id via Store join
- Updated scripts/slo_validator.py to use store_id via Store join
- Full test suite passes (200 tests, excluding e2e which requires running server)

## Task Commits

1. **Task 1: Update test_scrapers.py and create test_ingestor.py** - `14129fd` (feat)
2. **Task 2: Delete seed files, add smoke test, run full suite** - `14129fd` (feat, combined)

## Files Created/Modified
- `tests/test_ingestor.py` - Unit tests for ingest_rows, is_paddle, normalize
- `tests/test_pipeline_no_csv.py` - Smoke tests confirming no CSV dependencies
- `tests/test_scrapers.py` - Updated to mock ingest_rows instead of save_to_csv
- `app/api/routes.py` - Deprecated /admin/seed endpoint
- `scripts/quality_aggregator.py` - Updated to use store_id via Store join
- `scripts/slo_validator.py` - Updated to use store_id via Store join
- Deleted: app/data/brazil_pickleball_store.csv, app/data/joola_brazil.csv, app/data/paddle_stats_dump.csv, app/db/seed_brazil_catalog.py

## Decisions Made
- Deprecated /admin/seed endpoint — seeding now done via scrapers
- quality_aggregator and slo_validator use store_id via Store join

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- All seed CSVs removed, SCRP-01 complete
- Pipeline architecture is now 100% scraper-to-DB
- Ready for Phase 12 spec enrichment

---
*Phase: 11-seed-cleanup-store-catalog*
*Completed: 2026-03-21*
