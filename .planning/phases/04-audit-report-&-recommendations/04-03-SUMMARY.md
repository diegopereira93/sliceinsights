---
phase: 04-audit-report-&-recommendations
plan: "03"
subsystem: infra
tags: [docker, playwright, scrapers, runbook, operations]

requires:
  - phase: 04-01
    provides: AUDIT_REPORT.md with scraper health status and failure classifications
  - phase: 04-02
    provides: DATA_QUALITY.md with data quality findings
provides:
  - docs/operations/RUNBOOK_SCRAPERS.md — manual execution guide for all 11 scrapers
affects: [operations, future-scrapers, onboarding]

tech-stack:
  added: []
  patterns:
    - "Runbook pattern: per-scraper section with exact docker compose exec command, expected output, and troubleshooting"

key-files:
  created:
    - docs/operations/RUNBOOK_SCRAPERS.md
  modified: []

key-decisions:
  - "Runbook documents scraper-specific fixes inline (not generic) — each scraper has its own troubleshooting notes"
  - "Playwright fix documented as one-time environment fix affecting both justpaddles and fetch_johnkew"
  - "CSV ingesters shown with --dry-run flag to prevent accidental DB writes"

patterns-established:
  - "Operations docs live in docs/operations/ separate from audit docs in docs/audit/"

requirements-completed: [ART-05]

duration: 5min
completed: 2026-03-19
---

# Phase 4 Plan 03: Create Operational Runbook Summary

**290-line scraper runbook covering all 11 scrapers with exact docker compose exec commands, Playwright fix, CSV ingester argument usage, and 5-entry troubleshooting table**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-19T17:50:03Z
- **Completed:** 2026-03-19T17:55:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `docs/operations/RUNBOOK_SCRAPERS.md` with full scraper catalog (6 passing, 5 failing)
- Documented exact fix commands for all 3 failure categories (Playwright, CSV args, DNS/network)
- Added post-run DB verification commands and audit harness usage notes

## Task Commits

1. **Task 04-03-01: Create docs/operations/ and RUNBOOK_SCRAPERS.md** - `c25b6ce` (feat)

## Files Created/Modified

- `docs/operations/RUNBOOK_SCRAPERS.md` - 290-line manual execution runbook for all 11 scrapers

## Decisions Made

- Runbook documents scraper-specific fixes inline rather than generic troubleshooting — each scraper section is self-contained
- Playwright fix (`playwright install chromium`) documented once and cross-referenced for both affected scrapers
- CSV ingesters include `--dry-run` flag example to prevent accidental DB writes during manual testing

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 4 is now complete. All three deliverables are ready:
- `docs/AUDIT_REPORT.md` (04-01) — full scraper health audit with executive summary
- `docs/DATA_QUALITY.md` (04-02) — data quality findings with action items
- `docs/operations/RUNBOOK_SCRAPERS.md` (04-03) — operational runbook for manual execution

Recommended quick wins from the audit:
1. Run `playwright install chromium` in backend_v3 (fixes 2 scrapers, < 30 min)
2. Add minimum product count assertion to all scrapers (eliminates invisible failures)
3. Run US dump enrichment for 32 matched paddles (unblocks recommendation engine)

---
*Phase: 04-audit-report-&-recommendations*
*Completed: 2026-03-19*
