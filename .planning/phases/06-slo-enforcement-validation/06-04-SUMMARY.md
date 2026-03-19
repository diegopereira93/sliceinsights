---
phase: 6
plan: 4
subsystem: slo-enforcement
tags: [slo, scraper, real-time, non-blocking]
dependency_graph:
  requires: [06-02]
  provides: [real-time-slo-validation-hook]
  affects: [scripts/scraper_utils.py, scripts/run_scraper.py]
tech_stack:
  added: []
  patterns: [non-blocking-try-except, dispatcher-pattern, lazy-import]
key_files:
  created:
    - scripts/run_scraper.py
  modified:
    - scripts/scraper_utils.py
decisions:
  - finish_run() uses lazy import of slo_validator to avoid circular deps at module load
  - run_scraper.py created as new file (plan referenced non-existent scripts/run_scraper.py — treated as intent to create)
  - SLO check fires after module.main() returns, so data is committed before validation
metrics:
  duration_minutes: 15
  completed_date: "2026-03-19"
  tasks_completed: 3
  files_changed: 2
---

# Phase 6 Plan 4: Real-time SLO Validation Hook Summary

Real-time SLO validation integrated into scraper execution via `finish_run()` in `scraper_utils.py` and a new `run_scraper.py` dispatcher that calls it after each scraper's `main()` completes.

## What Was Built

- `scripts/scraper_utils.py` — added `finish_run(scraper_name: str)` function that prints a trace line and calls `validate_job_slo` in a try/except block
- `scripts/run_scraper.py` — new unified dispatcher mapping CLI scraper names to their modules, calling `finish_run()` after each scraper completes

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Lazy import of `slo_validator` inside `finish_run()` | Avoids circular import at module load time since `scraper_utils` is imported by scrapers which may be imported by `run_scraper` |
| Create `run_scraper.py` from scratch | Plan referenced this file as the integration target; it did not exist — intent was clear: create it |
| SLO hook fires after `module.main()` returns | Guarantees data is committed to DB before freshness check runs, so validation sees the new data |
| `finish_run()` in `scraper_utils.py` not in `run_scraper.py` | Makes the hook available to scrapers called directly (not via dispatcher), supporting both invocation paths |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `run_scraper.py` did not exist**
- **Found during:** Task 1
- **Issue:** Plan said "Modify `scripts/run_scraper.py`" but file did not exist in the repo
- **Fix:** Created `scripts/run_scraper.py` as a new dispatcher implementing the pattern described in the plan
- **Files modified:** `scripts/run_scraper.py` (created)
- **Commit:** e08e956

## Acceptance Criteria Verification

- [x] `scripts/run_scraper.py` calls `finish_run(scraper_name)` after each scraper completes
- [x] `scripts/scraper_utils.py` has `finish_run()` with SLO validation hook
- [x] Hook is wrapped in try/except (non-blocking)
- [x] Validation runs only for the specific scraper passed to `run_scraper`
- [x] `validate_job_slo` writes to `slo_logs` before scraper marks job complete (fires after `main()` returns)
- [x] Trace line: `[SLO] SLO validation triggered for {scraper_name}`

## Self-Check: PASSED

Files exist:
- `scripts/run_scraper.py` — created
- `scripts/scraper_utils.py` — modified (finish_run added)

Commits:
- e08e956 — feat(06-04): add finish_run() SLO hook and run_scraper.py entry point
