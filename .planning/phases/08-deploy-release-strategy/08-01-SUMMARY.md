---
phase: 08-deploy-release-strategy
plan: 01
subsystem: database
tags: [sqlmodel, alembic, postgresql, deploy, versioning, validation]

requires:
  - phase: 07-alerts-monitoring
    provides: slo_logs table with scraper_name/status/checked_at used by SLO gate query
  - phase: 06-slo-enforcement
    provides: SLOLog model, slo_validator.py, sync_engine pattern

provides:
  - DeployLog ORM model (deploy_logs table) with full batch lifecycle fields
  - version_id column on market_offers and paddle_master for flag-flip rollback
  - market_offers_staging table for batch isolation before publish
  - Alembic migration a3f9c1d82e47 chaining from d081a2cccc0e
  - deploy_validator.py with check_slo_gate, run_corruption_audit, run_pre_deploy_validation
  - 15 unit tests covering model fields, SLO gate, corruption audit, combined validation

affects:
  - 08-02 (batch aggregation writes to market_offers_staging with batch_id)
  - 08-03 (publish reads from staging, updates version_id on production tables)
  - 08-04 (rollback filters market_offers by version_id)
  - 08-05 (workflow calls run_pre_deploy_validation before publish step)

tech-stack:
  added: []
  patterns:
    - SQLModel table=True with Optional[int] = None for nullable FK-like versioning columns
    - Session(sync_engine) context manager pattern for scripts using raw SQL via text()
    - TDD with mock session (session.execute.side_effect list) for DB-free unit tests
    - Alembic migration using op.create_table + op.add_column with server_default

key-files:
  created:
    - app/models/deploy_log.py
    - alembic/versions/a3f9c1d82e47_add_deploy_versioning.py
    - scripts/deploy_validator.py
    - tests/test_deploy_validator.py
    - tests/test_deploy_models.py
  modified:
    - app/models/market_offer.py
    - app/models/paddle.py
    - app/models/__init__.py
    - app/db/database.py
    - alembic/env.py

key-decisions:
  - "DeployLog uses timezone.utc via lambda for created_at (avoids deprecated datetime.utcnow)"
  - "version_id added only to MarketOffer table class (not MarketOfferBase) to avoid affecting API input schemas"
  - "PaddleMaster rollback uses version_id only — no is_active column added (plan explicitly forbids it)"
  - "check_slo_gate uses two separate queries (passed + failed) for clarity over a single GROUP BY query"
  - "run_corruption_audit uses raw SQL text() queries rather than ORM for staging table (no ORM model for staging)"

patterns-established:
  - "Deploy scripts import sync_engine and use Session(sync_engine) as context manager with raw text() queries"
  - "Validation functions return (bool, list[str]) tuple — caller aggregates all failures before returning"
  - "TDD tests mock session.execute.side_effect as list to simulate sequential DB queries"

requirements-completed: [DEP-01, DEP-02, DEP-05]

duration: 4min
completed: 2026-03-20
---

# Phase 08 Plan 01: Deploy Database Foundation Summary

**DeployLog SQLModel + version_id columns on market_offers/paddle_master + staging table + Alembic migration a3f9c1d82e47 + dual SLO/corruption pre-deploy validator with 15 passing tests**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-20T00:35:36Z
- **Completed:** 2026-03-20T00:39:43Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- DeployLog ORM model created with all 11 fields (batch_id, version_id, status, scrapers_passed, scrapers_total, products_published, forced, operator_id, created_at, finished_at, failure_reason)
- Alembic migration a3f9c1d82e47 creates deploy_logs and market_offers_staging tables and adds version_id to market_offers and paddle_master
- deploy_validator.py implements dual validation: SLO day-window gate via slo_logs + NULL corruption audit on staging table; CLI exits 0/1

## Task Commits

1. **Task 1: DeployLog model, version_id columns, staging table, Alembic migration** - `91892e1` (feat)
2. **Task 2: Pre-deploy validation script with unit tests** - `66a593d` (feat)

## Files Created/Modified

- `app/models/deploy_log.py` - DeployLog SQLModel table class (deploy_logs)
- `alembic/versions/a3f9c1d82e47_add_deploy_versioning.py` - Migration: adds version_id cols, creates staging + deploy_logs tables (down_revision: d081a2cccc0e)
- `app/models/market_offer.py` - Added version_id: Optional[int] = None to MarketOffer and MarketOfferRead
- `app/models/paddle.py` - Added version_id: Optional[int] = None to PaddleMaster
- `app/models/__init__.py` - Added DeployLog export
- `app/db/database.py` - Registered DeployLog for SQLModel metadata
- `alembic/env.py` - Registered DeployLog for autogenerate metadata
- `scripts/deploy_validator.py` - check_slo_gate + run_corruption_audit + run_pre_deploy_validation + CLI
- `tests/test_deploy_validator.py` - 10 unit tests (mock-based, no live DB)
- `tests/test_deploy_models.py` - 5 model unit tests

## Decisions Made

- DeployLog `created_at` uses `lambda: datetime.now(timezone.utc)` to avoid the deprecated `datetime.utcnow()` — consistent with modern Python datetime best practices
- `version_id` added only to the `MarketOffer` table class (not `MarketOfferBase`) so API input schemas are unaffected
- PaddleMaster rollback uses `version_id` only — no `is_active` column added per plan specification
- `run_corruption_audit` uses raw `text()` SQL for staging queries — no ORM model exists for `market_offers_staging`
- Two separate SELECT queries in `check_slo_gate` (passed + failed) rather than GROUP BY for testability and readability

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Alembic migration must be run against the production DB before Phase 8 deploy tasks execute (`alembic upgrade head`).

## Next Phase Readiness

- All database foundations are in place for Phase 8 plans 02-05
- 08-02 (batch aggregation) can write to `market_offers_staging` with `batch_id`
- 08-03 (publish) can call `run_pre_deploy_validation` then move rows from staging to production with `version_id`
- 08-04 (rollback) can filter `market_offers` by `version_id` to revert
- 08-05 (workflow) can wire all pieces together using `DeployLog` for audit trail

---
*Phase: 08-deploy-release-strategy*
*Completed: 2026-03-20*
