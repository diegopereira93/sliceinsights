---
phase: 12-spec-enrichment-scrapers
plan: "02"
subsystem: infra
tags: [scraper, playwright, beautifulsoup, requests, stores]

# Dependency graph
requires:
  - phase: 12-spec-enrichment-scrapers
    provides: update_paddle_specs(), weight_grams column, 4-field gate
provides:
  - 8 new store spec extractors (yosports, supremo, shark, prospin, drop_shot_brasil, just_paddles, pcklhouse, propadel)
  - STORE_HANDLERS dict with all 10 stores (async/sync routing)
  - Complete 10-store routing in main()
affects: [12-spec-enrichment-scrapers]

# Tech tracking
tech-stack:
  added: [beautifulsoup, requests, playwright async]
  patterns: [store routing dict, async/sync handler dispatch, BS4 spec extraction]

key-files:
  created: []
  modified:
    - scripts/scrape_product_specs.py
    - tests/test_spec_enricher.py

key-decisions:
  - "Used STORE_HANDLERS dict to decouple store slugs from scraping functions — extensible for new stores"
  - "Used globals()[handler_name] for dynamic handler dispatch — keeps routing clean"
  - "Used store_id->slug mapping (id_to_slug) from STORE_SLUG_TO_ID to route all 10 stores"

patterns-established:
  - "STORE_HANDLERS dict: maps slug -> {func, async} for all 10 stores"
  - "BS4 store extractors: structured table parsing + freetext fallback"

requirements-completed: [SCRP-02, SCRP-03, SCRP-04, SCRP-05]

# Metrics
duration: 15min
completed: 2026-03-21
---

# Phase 12, Plan 02: 8 Store Spec Extractors + All 10 Stores Registered

**All 10 BR store spec extractors implemented and registered in STORE_HANDLERS: 6 BS4/requests extractors (yosports, supremo, shark, prospin, pcklhouse, propadel) + 2 Playwright async extractors (drop_shot_brasil, just_paddles).**

## Performance

- **Duration:** 15 min
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added 6 BS4/requests spec extractors for: yosports, supremo, shark, prospin, pcklhouse, propadel
- Each extractor fetches product page HTML, parses structured tables (WooCommerce attribute tables) or freetext descriptions
- Added 2 Playwright async extractors: drop_shot_brasil, just_paddles
- Extended `STORE_SLUG_TO_ID` with all 10 store IDs
- Created `STORE_HANDLERS` dict with all 10 stores, async/sync flag, and function name
- Refactored `main()` to route all stores via `STORE_HANDLERS`
- Added `store_slug` field to target dicts for routing
- 33 spec enricher tests pass, 233 total tests pass

## Task Commits

1. **Task 1: Add 6 BS4/requests store extractors** — `47c54a5` (feat)
2. **Task 2: Add 2 Playwright extractors + register all 10 stores** — `af2a788` (feat)

## Files Modified

- `scripts/scrape_product_specs.py` — 8 new store spec extractors, STORE_SLUG_TO_ID, STORE_HANDLERS, updated main() routing
- `tests/test_spec_enricher.py` — 7 new tests for store extractors and STORE_HANDLERS

## Decisions Made

- Used `globals()[handler_name]` for dynamic handler dispatch — simple and extensible
- Used `store_id` → `slug` mapping from `STORE_SLUG_TO_ID` to route all stores without hardcoding URLs
- WooCommerce stores (shark, prospin): structured table parsing first, freetext fallback
- Nuvemshop/custom stores: freetext parsing via `parse_freetext_specs()`

## Deviations from Plan

None - plan executed as written.

## Issues Encountered

None.

## Next Phase Readiness

- Plan 12-03 (GHA workflow) can proceed — `scrape_product_specs.py --store` interface is fully functional for all 10 stores

---
*Phase: 12-spec-enrichment-scrapers*
*Completed: 2026-03-21*
