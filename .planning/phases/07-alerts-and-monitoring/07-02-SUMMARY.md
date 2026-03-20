---
phase: 07-alerts-monitoring
plan: 02
subsystem: alerts
tags: [slo, alerts, alert-worker, github-actions, dedup, cli]
dependency_graph:
  requires: [app/services/slo_alerts.py, app/models/slo_alert.py, app/models/slo.py, app/db/database.py]
  provides: [scripts/alert_worker.py, tests/test_alert_worker.py]
  affects: [.github/workflows/slo-check.yml]
tech_stack:
  added: []
  patterns: [argparse CLI (mirrors slo_validator.py), session-injected dedup functions, TDD red-green, GitHub Actions multi-job with needs/if-always]
key_files:
  created:
    - scripts/alert_worker.py
    - tests/test_alert_worker.py
  modified:
    - .github/workflows/slo-check.yml
decisions:
  - "LOOKBACK_HOURS=7 chosen to slightly exceed the 6h cron cycle and avoid edge-case gaps"
  - "process_passes deduplicates by (scraper_name, metric_type) set to avoid redundant clear_alert_throttle calls"
  - "alert job uses if: always() so it runs even when slo-check job itself fails (breach data still in slo_logs)"
  - "GITHUB_REPOSITORY uses github.repository context variable (auto-set by Actions, not a secret)"
metrics:
  duration_seconds: 180
  completed_date: "2026-03-19"
  tasks_completed: 2
  files_created: 2
  files_modified: 1
---

# Phase 07 Plan 02: Wire Alert Worker into Pipeline Summary

**One-liner:** alert_worker.py CLI bridges slo_logs FAIL entries to SLOAlertService dispatch with 24h dedup, plus GitHub Actions alert job wired after slo-check with all 10 required secrets.

## What Was Built

- **`scripts/alert_worker.py`** — CLI entrypoint (`--all` / `--scraper`) that queries slo_logs for FAIL entries within a 7h lookback, converts each to `SLOBreach`, applies 24h dedup via `should_send_alert`, dispatches via `SLOAlertService.notify`, upserts dedup record, and clears throttle for PASS/SKIP resolutions
- **`tests/test_alert_worker.py`** — 12 unit tests covering field mapping, query filtering, throttle logic, resolution detection, exception handling, LOOKBACK_HOURS constant, and main() orchestration
- **`.github/workflows/slo-check.yml`** — Extended with `alert` job: `needs: slo-check`, `if: always()`, `continue-on-error: true`, 10 env vars injected as secrets

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create alert_worker.py CLI (TDD) | bba8b2a | scripts/alert_worker.py, tests/test_alert_worker.py |
| 2 | Extend slo-check.yml with alert job | 7178496 | .github/workflows/slo-check.yml |
| 3 | Human verification checkpoint | — | (awaiting human approval) |

## Decisions Made

1. **LOOKBACK_HOURS=7** — Slightly more than the 6h cron cycle to avoid missing breaches written at the end of the prior slo-check run.
2. **process_passes dedup set** — Tracks `(scraper_name, metric_type)` pairs already cleared to avoid calling `clear_alert_throttle` multiple times per pass run.
3. **if: always() on alert job** — Ensures the alert job runs even when slo-check fails, so pre-existing breach data in slo_logs still gets processed.
4. **GITHUB_REPOSITORY via github.repository** — Uses the built-in Actions context variable rather than a secret, since it's not sensitive.

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

```
39 passed, 8 warnings in 0.43s
  — 27 service tests (tests/test_slo_alerts.py)
  — 12 worker tests (tests/test_alert_worker.py)

alert_worker.py refs in slo-check.yml:    1
TELEGRAM_BOT_TOKEN in slo-check.yml:      1
continue-on-error: true count:            2 (one per job)
needs: slo-check:                         1
if: always():                             1
```

## Self-Check: PASSED

- FOUND: scripts/alert_worker.py
- FOUND: tests/test_alert_worker.py
- FOUND: .github/workflows/slo-check.yml (modified)
- FOUND commit: bba8b2a (Task 1)
- FOUND commit: 7178496 (Task 2)
