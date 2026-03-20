---
phase: 08-deploy-release-strategy
plan: "02"
subsystem: deploy-worker
tags: [deploy, batch, publish, rollback, force-publish, versioning, cli]
dependency_graph:
  requires: ["08-01"]
  provides: ["scripts/deploy_worker.py", "deploy_worker CLI"]
  affects: ["market_offers", "market_offers_staging", "deploy_logs"]
tech_stack:
  added: []
  patterns: ["TDD red-green", "atomic transactions via sync_engine.begin()", "argparse mutually exclusive group", "flag-flip rollback"]
key_files:
  created:
    - scripts/deploy_worker.py
    - tests/test_deploy_worker.py
  modified: []
decisions:
  - "SLOAlertService imported at module level (not lazily) — plan said lazy import to avoid circular, but import chain analysis showed no circular dependency; module-level import is cleaner and testable"
  - "force_publish uses sync_engine.begin() for publish then Session for audit log — consistent with rollback_batch pattern; separates atomic write from ORM audit"
  - "aggregate_batch accepts passed_scrapers list from caller — avoids redundant SLO gate query inside aggregate; caller (run_deploy) controls the gate"
metrics:
  duration_minutes: 25
  completed_date: "2026-03-19"
  tasks_completed: 1
  tasks_total: 1
  files_created: 2
  files_modified: 0
  tests_added: 21
  tests_passing: 21
---

# Phase 8 Plan 02: Deploy Worker Summary

**One-liner:** Deploy worker with atomic batch publish (staging upsert + version tagging), flag-flip rollback, force-publish audit trail, old version pruning, and argparse CLI operator tool.

## What Was Built

`scripts/deploy_worker.py` is the operational heart of Phase 8. It implements the complete nightly deploy lifecycle:

| Function | Purpose |
|---|---|
| `generate_batch_id(batch_date)` | Returns `batch_YYYYMMDD_<6hex>` identifier |
| `get_next_version_id(conn)` | COALESCE(MAX(version_id),0)+1 from published deploy_logs |
| `cleanup_old_staging(conn, days=7)` | TTL cleanup of staging rows older than 7 days |
| `aggregate_batch(conn, batch_id, batch_date, passed_scrapers)` | INSERT INTO market_offers_staging scoped to calendar day, per SLO-passing scraper |
| `publish_batch(conn, batch_id, version_id)` | Deactivates prev version, upserts staging to market_offers with ON CONFLICT |
| `rollback_batch(batch_id)` | Flag-flip: current version is_active=false, previous is_active=true |
| `force_publish(batch_id, operator_id)` | Bypasses validation, sets forced=True and operator_id in DeployLog, sends Telegram alert |
| `prune_old_versions(conn, current_version_id)` | Deletes rows with version_id < (current - 1) |
| `run_deploy(batch_date)` | Full orchestration: SLO gate -> staging -> pending log -> validate -> publish -> prune |
| `_build_parser()` | argparse with --run/--validate-batch/--force-publish/--rollback (mutually exclusive) |
| `main()` | CLI dispatcher with try/except and sys.exit codes |

## Tests

21 unit tests in `tests/test_deploy_worker.py`, all passing:

- Tests 1-2: `generate_batch_id` pattern matching (`batch_YYYYMMDD_[0-9a-f]{6}`)
- Tests 3-4: `get_next_version_id` — empty table returns 1, increments max
- Tests 5-6: `aggregate_batch` — inserts per scraper, returns (count, scrapers), handles empty list
- Tests 7-8: `publish_batch` — 2 SQL calls (deactivate + upsert), returns rowcount
- Tests 9-10: `rollback_batch` — calls execute, writes DeployLog with status='rolled_back'
- Tests 11-12: `force_publish` — sets forced=True/operator_id, sends Telegram alert
- Tests 13-14: `prune_old_versions` — DELETE SQL called, returns rowcount
- Tests 15-19: CLI parser — --run, --rollback, --force-publish, --validate-batch, mutual exclusion
- Tests 20-21: CLI dispatch — main() routes to run_deploy and rollback_batch correctly

## Deviations from Plan

### Auto-fixed Issues

None — plan executed as written.

### Minor Implementation Notes

**SLOAlertService import:** Plan suggested lazy import inside `force_publish` to avoid circular imports. Import chain analysis showed no circular dependency (deploy_worker -> slo_alerts, which has no back-reference). Used module-level import for cleaner, testable code.

**run_deploy session management:** Plan described `conn` for both SLO gate and aggregation. `check_slo_gate` accepts a `Session`, not a raw connection. Split: SQLAlchemy `Session` for ORM queries, `sync_engine.begin()` for raw SQL writes — consistent with deploy_validator.py pattern.

## Self-Check

- [x] `scripts/deploy_worker.py` exists
- [x] `tests/test_deploy_worker.py` exists
- [x] All required functions present (`generate_batch_id`, `get_next_version_id`, `aggregate_batch`, `publish_batch`, `rollback_batch`, `force_publish`, `prune_old_versions`, `run_deploy`, `_build_parser`)
- [x] CLI flags: `--run`, `--validate-batch`, `--force-publish`, `--rollback`
- [x] `from app.db.database import sync_engine` present
- [x] `INSERT INTO market_offers_staging` present
- [x] `ON CONFLICT` / `DO UPDATE SET` present
- [x] `UPDATE market_offers SET is_active = false` present
- [x] `status="rolled_back"` present
- [x] `forced=True` present
- [x] 21 test functions (>= 10 required)
- [x] pytest exits code 0

## Self-Check: PASSED
