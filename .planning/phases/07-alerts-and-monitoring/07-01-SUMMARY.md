---
phase: 07-alerts-monitoring
plan: 01
subsystem: alerts
tags: [slo, alerts, telegram, github-issues, email, dedup, orm]
dependency_graph:
  requires: [app/models/slo.py, app/db/database.py, alembic/env.py]
  provides: [app/models/slo_alert.py, app/services/slo_alerts.py, tests/test_slo_alerts.py]
  affects: [app/db/database.py, alembic/env.py, requirements.txt]
tech_stack:
  added: [PyGithub==2.8.1]
  patterns: [SQLModel ORM table, dataclass with property, module-level dedup functions, smtplib STARTTLS, PyGithub Auth.Token]
key_files:
  created:
    - app/models/slo_alert.py
    - app/services/slo_alerts.py
    - tests/test_slo_alerts.py
  modified:
    - app/db/database.py
    - alembic/env.py
    - requirements.txt
decisions:
  - "SLOBreach dataclass placed in slo_alert.py alongside SLOAlert model for cohesion"
  - "Dedup functions are module-level (not class methods) to simplify unit testing with mock sessions"
  - "PyGithub installed into venv immediately after adding to requirements.txt (Rule 3: blocking dependency)"
  - "THROTTLE_HOURS=24 constant exported for test assertions"
metrics:
  duration_seconds: 221
  completed_date: "2026-03-19"
  tasks_completed: 3
  files_created: 3
  files_modified: 3
---

# Phase 07 Plan 01: SLO Alert Foundation Summary

**One-liner:** Multi-channel SLO alert service (Telegram + GitHub Issues + Email) with 24h dedup throttle via SQLModel ORM, dispatching P1/P2/P3 severity routing and 27 unit tests with mocked external calls.

## What Was Built

- **`app/models/slo_alert.py`** — `SLOAlert` SQLModel table for dedup state tracking (`slo_alerts`); `SLOBreach` dataclass with `severity` property deriving P1/P2/P3 from `metric_type`
- **`app/services/slo_alerts.py`** — `SLOAlertService` with `notify()` fan-out to Telegram, GitHub Issues, and Email; module-level `should_send_alert`, `upsert_alert_record`, `clear_alert_throttle` with 24h throttle window; `get_slo_alert_service()` factory from env vars
- **`tests/test_slo_alerts.py`** — 27 unit tests covering all channels, routing, graceful degradation, dedup, and message content (all pass)

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create SLOAlert model and SLOBreach dataclass | 7fc7d49 | app/models/slo_alert.py, app/db/database.py, alembic/env.py, requirements.txt |
| 2 | Implement SLOAlertService with 3 channels | c5955fb | app/services/slo_alerts.py |
| 3 | Write 27 comprehensive unit tests | df702b1 | tests/test_slo_alerts.py |

## Decisions Made

1. **SLOBreach in slo_alert.py** — Dataclass lives alongside the ORM model rather than in services for cohesion; both are imported together by consumers.
2. **Module-level dedup functions** — `should_send_alert`, `upsert_alert_record`, `clear_alert_throttle` are module-level functions (not class methods) so tests can inject a mock `Session` directly without instantiating the service.
3. **PyGithub installed immediately** — Added to venv during Task 2 execution (not deferred) to unblock import verification.
4. **THROTTLE_HOURS exported** — Makes the 24h constant testable and allows Plan 02 to reference the canonical value.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] PyGithub not installed in venv**
- **Found during:** Task 2 verification
- **Issue:** `PyGithub==2.8.1` was added to `requirements.txt` but not installed in the project venv, causing `ModuleNotFoundError: No module named 'github'`
- **Fix:** Ran `.venv/bin/pip install PyGithub==2.8.1`
- **Files modified:** None (runtime fix only; requirements.txt already correct)
- **Commit:** inline, no separate commit needed

## Verification Results

```
model OK         — app/models/slo_alert.py imports cleanly
service OK       — app/services/slo_alerts.py imports cleanly
PyGithub: 1      — requirements.txt contains PyGithub==2.8.1
SLOAlert in DB: 1  — app/db/database.py registers SLOAlert
SLOAlert in alembic: 1  — alembic/env.py registers SLOAlert
27 passed        — all unit tests pass (0.40s)
```

## Self-Check: PASSED

- FOUND: app/models/slo_alert.py
- FOUND: app/services/slo_alerts.py
- FOUND: tests/test_slo_alerts.py
- FOUND commit: 7fc7d49 (Task 1)
- FOUND commit: c5955fb (Task 2)
- FOUND commit: df702b1 (Task 3)
