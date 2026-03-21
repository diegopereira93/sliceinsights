---
phase: 12-spec-enrichment-scrapers
plan: "03"
subsystem: infra
tags: [github-actions, workflow, cron, ci]

# Dependency graph
requires:
  - phase: 12-spec-enrichment-scrapers
    provides: scrape_product_specs.py with --store interface, quality_aggregator.py
provides:
  - Weekly GHA workflow for spec enrichment with 10-store matrix
  - Post-enrichment quality audit automation
affects: []

# Tech tracking
tech-stack:
  added: [GitHub Actions, cron scheduling]
  patterns: [matrix-based CI, continue-on-error, always-run consolidation]

key-files:
  created:
    - .github/workflows/scrape-enrichment.yml
  modified: []

key-decisions:
  - "Weekly cron at Monday 06:00 UTC — early morning in Brazil, before weekday usage"
  - "Playwright installed for ALL matrix jobs — simpler than conditional installs"
  - "Separate workflow from quality-audit.yml — enrichment is a distinct concern"

patterns-established:
  - "GHA matrix workflow: continue-on-error + fail-fast: false for resilient multi-store scraping"

requirements-completed: [SCRP-02, SCRP-06]

# Metrics
duration: 5min
completed: 2026-03-21
---

# Phase 12, Plan 03: Weekly Spec Enrichment GitHub Actions Workflow

**Weekly GitHub Actions workflow (scrape-enrichment.yml) triggers all 10 store spec enrichers every Monday 06:00 UTC with post-enrichment quality audit.**

## Performance

- **Duration:** 5 min
- **Tasks:** 1
- **Files created:** 1

## Accomplishments
- Created `.github/workflows/scrape-enrichment.yml` with all required structure
- Weekly cron at Monday 06:00 UTC
- `workflow_dispatch` for manual triggering
- 10-store matrix with `continue-on-error: true` and `fail-fast: false`
- Playwright Chromium installed before all enrichment jobs
- Post-enrichment quality audit via `quality_aggregator.py --consolidate`
- Audit job runs even on enrichment failures (`if: always()`)
- All workflow structural checks pass

## Task Commits

1. **Task 1: Create weekly spec enrichment GitHub Actions workflow** — `635704c` (feat)

## Files Created

- `.github/workflows/scrape-enrichment.yml` — Weekly enrichment workflow with 10-store matrix + post-enrichment audit

## Decisions Made

- `cron: '0 6 * * 1'` (Monday 06:00 UTC) — early morning BR time before weekday usage
- Playwright installed for ALL jobs (not conditional) — simpler, ~30s overhead per job
- Separate from `quality-audit.yml` — enrichment and quality audit are distinct concerns

## Deviations from Plan

None - plan executed as written.

## Issues Encountered

None.

## Next Phase Readiness

- Phase 12 complete — all 3 plans executed
- Ready for verification and roadmap update

---
*Phase: 12-spec-enrichment-scrapers*
*Completed: 2026-03-21*
