---
phase: 11-seed-cleanup-store-catalog
plan: "02"
subsystem: database
tags: [sqlmodel, scraper, ingestor, postgresql, upsert]

requires:
  - phase: "11-01"
    provides: "Store model and store_id FK on MarketOffer"
provides:
  - Shared ingestor module with brand/paddle dedup and MarketOffer upsert
  - All 9 scrapers adapted from CSV to DB writes via ingest_rows
affects: [12-spec-enrichment, 11-03]

tech-stack:
  added: [sqlmodel, sqlalchemy-upsert]
  patterns: [scraper-to-db-pipeline, get-or-create-pattern]

key-files:
  created:
    - app/db/ingestor.py
  modified:
    - scripts/scrape_brazil_store.py
    - scripts/scrape_joola.py
    - scripts/scrape_yosports.py
    - scripts/scrape_supremo.py
    - scripts/scrape_shark.py
    - scripts/scrape_prospin.py
    - scripts/scrape_dropshot_brasil.py
    - scripts/scrape_pcklhouse.py
    - scripts/scrape_propadel.py

key-decisions:
  - "Kept save_to_csv in scraper_utils.py for debug use"
  - "Each scraper uses STORE_NAME constant matching stores table exactly"

patterns-established:
  - "Ingestor pattern: get-or-create Brand, get-or-create PaddleMaster, upsert MarketOffer"

requirements-completed: [SCRP-01, STORE-02]

duration: 20min
completed: 2026-03-21
---

# Phase 11: Shared DB Ingestor & Adapted Scrapers Summary

**Shared ingestor module with brand/paddle dedup and upsert; 9 scrapers now write directly to DB via ingest_rows()**

## Performance

- **Duration:** 20 min
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Created ingestor module with `ingest_rows()` supporting brand/paddle deduplication and MarketOffer upsert
- Added `is_paddle()` filter to skip accessories (bags, balls, etc.)
- Adapted all 9 scrapers from `save_to_csv` to `ingest_rows()` DB writes
- Each scraper uses `STORE_NAME` constant matching stores table exactly
- Kept `save_to_csv` in `scraper_utils.py` for debug use
- Verified `run_scraper.py` does not reference `seed_brazil_catalog`

## Task Commits

1. **Task 1: Create shared ingestor module** - `1998451` (feat)
2. **Task 2: Adapt all 10 scrapers and run_scraper.py** - `1998451` (feat, combined)

## Files Created/Modified
- `app/db/ingestor.py` - Shared DB write logic with ingest_rows, is_paddle, normalize
- `scripts/scrape_brazil_store.py` - Adapted to use ingest_rows
- `scripts/scrape_joola.py` - Adapted to use ingest_rows
- `scripts/scrape_yosports.py` - Adapted to use ingest_rows
- `scripts/scrape_supremo.py` - Adapted to use ingest_rows
- `scripts/scrape_shark.py` - Adapted to use ingest_rows
- `scripts/scrape_prospin.py` - Adapted to use ingest_rows
- `scripts/scrape_dropshot_brasil.py` - Adapted to use ingest_rows
- `scripts/scrape_pcklhouse.py` - Adapted to use ingest_rows
- `scripts/scrape_propadel.py` - Adapted to use ingest_rows

## Decisions Made
- Kept `save_to_csv` in scraper_utils.py for debug use
- Each scraper uses STORE_NAME constant matching stores table exactly

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Pipeline architecture is now scraper -> DB (no CSV in data path)
- Ready for Phase 11-03 (remove seed CSVs)
- JustPaddles scraper already uses DB directly (Paddle Lab spec scraper)

---
*Phase: 11-seed-cleanup-store-catalog*
*Completed: 2026-03-21*
