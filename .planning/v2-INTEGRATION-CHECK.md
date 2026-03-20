# Integration Check: SliceInsights v2.0 Milestone

**Date:** 2026-03-20
**Scope:** Phases 05, 06, 07, 08, 09, 10

---

## Wiring Summary

**Connected:** 8 exports properly used
**Orphaned:** 0 exports created but unused
**Missing:** 1 expected connection not found

## API / Script Coverage

**Consumed:** 5 scripts wired into workflows or callers
**Orphaned:** 0 scripts with no callers

## Auth Protection

N/A — this is a data-pipeline system, no user auth surface.

## E2E Flows

**Complete:** 3 flows work end-to-end
**Broken:** 1 flow has a break (Phase 10 fix uncommitted)

---

## Detailed Findings

### Connected Exports (verified by grep)

| Export | From | Used By | Evidence |
|--------|------|---------|----------|
| `validate_job_slo()` | Phase 06 `slo_validator.py` | Phase 06 `scraper_utils.py:finish_run()` | lazy import at line 488 |
| `slo_logs` table | Phase 06 `app/models/slo.py` | Phase 07 `alert_worker.py` (queries `SLOLog.status=='fail'`) | lines 45-46 |
| `slo_logs` table | Phase 06 `app/models/slo.py` | Phase 08 `deploy_validator.py:check_slo_gate()` (queries `status='pass'`) | line 46 |
| `SLOAlertService` | Phase 07 `app/services/slo_alerts.py` | Phase 07 `alert_worker.py` import line 24 | confirmed |
| `SLOAlertService` | Phase 07 `app/services/slo_alerts.py` | Phase 08 `deploy_worker.py:force_publish()` | module-level import line 34 |
| `check_slo_gate()` | Phase 08 `deploy_validator.py` | Phase 08 `deploy_worker.py` import line 34, call line 348 | confirmed |
| `run_pre_deploy_validation()` | Phase 08 `deploy_validator.py` | Phase 08 `deploy_worker.py` call line 391 + CLI line 506 | confirmed |
| `QualityMetric` model | Phase 09 `app/models/quality_metric.py` | Phase 09 `quality_aggregator.py` | import line 32, used throughout |

### Missing Connections

**1. CI workflow does not cover Phase 10 test file `tests/test_slo_validator.py`**

- The CI job runs `pytest tests/ --ignore=tests/test_e2e_api.py` — this glob covers `test_slo_validator.py` only once it is committed.
- `tests/test_slo_validator.py` is currently **untracked** (Phase 10 uncommitted). Until Phase 10 is committed, this file is not on disk in CI and the 6 new tests do not run in CI.
- Affected requirements: **SLO-03, DEP-01**

**2. `deploy-nightly.yml` does not call `deploy_validator.py` directly — it calls `deploy_worker.py --run`**

- This is architecturally correct: `deploy_worker.run_deploy()` internally calls `run_pre_deploy_validation()`. The wiring is through Python call chain, not shell. Not a bug — but worth noting for auditability.
- No broken connection; wiring is indirect but confirmed.

**3. `quality_aggregator.py` does not cross-call `slo_validator.py`**

- Phase 09 computes freshness independently from `market_offers.last_updated` (same raw data source as Phase 06). There is no shared call or dedup between the two systems.
- This is a **scope overlap**, not a broken wire: both systems independently read the same table column. Values should be consistent but are computed twice with separate logic.
- Affected requirements: **QC-01, QC-02 vs SLO-03** — if thresholds diverge in future, inconsistency risk.

### Broken Flows

**Flow: Scraper run → SLO check → Nightly deploy (SLO gate)**

| Step | Status | Detail |
|------|--------|--------|
| Scraper writes `market_offers` | COMPLETE | scraper → `finish_run()` |
| `finish_run()` calls `validate_job_slo()` | COMPLETE | `scraper_utils.py:488` |
| `validate_job_slo()` writes `slo_logs` row | COMPLETE | `slo_validator.py` |
| `slo_logs` row has `status='pass'` when fresh | **BROKEN in committed code** | `check_freshness()` wrote `status='skip'` instead of `'pass'`; fix exists in working tree but is **uncommitted** |
| `check_slo_gate()` finds pass rows for deploy | **BLOCKED** | queries `status='pass'`; finds zero rows from freshness checks while fix is uncommitted |
| `deploy_worker.run_deploy()` proceeds | **BLOCKED** | `run_deploy()` aborts with "No scrapers passed SLO gate" |

**Root cause:** `scripts/slo_validator.py` has the fix (`status='pass'`) in the working tree (modified, not staged) and in `tests/test_slo_validator.py` (untracked). Until these are committed and pushed, `CI` runs against the pre-fix code on `HEAD`, and the production nightly deploy is broken.

**Affected requirements: SLO-03, DEP-01**

### Complete Flows

**Flow 1: Scraper run → SLO check → Alert dispatch**

`scraper → finish_run() → validate_job_slo() → slo_logs (status='fail') → alert_worker.py get_recent_failures() → SLOAlertService.notify() → Telegram/GitHub/Email`

All links confirmed by grep. Non-blocking design (try/except in finish_run, continue-on-error in slo-check.yml). COMPLETE.

**Flow 2: Pre-deploy validation → Publish → Audit log**

`deploy_worker.run_deploy() → check_slo_gate() [slo_logs] → aggregate_batch() [staging] → run_pre_deploy_validation() → publish_batch() → DeployLog write`

All function calls confirmed by grep in `deploy_worker.py`. COMPLETE (modulo broken SLO gate above).

**Flow 3: Quality metric computation → Report**

`quality_aggregator.py --all → compute_metrics() [market_offers] → persist_metrics() [quality_metrics table] → quality_report.py`

Confirmed by grep in `quality_aggregator.py`. COMPLETE.

### Unprotected Routes

N/A — no HTTP routes in this system.

---

## CI/CD Pipeline Coverage

| Deliverable | Covered by CI | Notes |
|-------------|--------------|-------|
| `scripts/slo_validator.py` tests | YES (once Phase 10 committed) | `test_slo_validator.py` untracked; CI would run it after commit |
| `scripts/deploy_validator.py` tests | YES | `tests/test_deploy_validator.py` is tracked (modified, not new) |
| `scripts/deploy_worker.py` tests | YES | `tests/test_deploy_worker.py` tracked |
| `app/services/slo_alerts.py` tests | YES | `tests/test_slo_alerts.py` tracked |
| `scripts/quality_aggregator.py` tests | YES | `tests/test_quality_aggregator.py` tracked |
| Smoke test (`smoke_test_quality.py`) | YES | job 2 in `ci.yml` |
| `deploy-nightly.yml` integration | NO | not triggered by CI; requires `repository_dispatch` or manual trigger |

**Gap:** CI unit-test job runs `pytest tests/` which will pick up `test_slo_validator.py` after commit, but the file is currently untracked. The 6 Phase 10 tests are not running in CI today.

---

## Requirements Integration Map

| Requirement | Integration Path | Status | Issue |
|-------------|-----------------|--------|-------|
| SLO-01 | `finish_run()` → `validate_job_slo()` → `slo_logs` | WIRED | None |
| SLO-02 | `slo-check.yml` cron → `slo_validator.py --all` → `slo_logs` | WIRED | None |
| SLO-03 | `check_freshness()` → `slo_logs(status='pass')` → `check_slo_gate()` | PARTIAL | Fix in working tree, uncommitted; gate broken in HEAD |
| DEP-01 | `check_slo_gate()` finds pass rows → `aggregate_batch()` → nightly publish | PARTIAL | Blocked by SLO-03 bug in HEAD |
| DEP-02 | `run_pre_deploy_validation()` called in `run_deploy()` before publish | WIRED | None |
| DEP-03 | `publish_batch()` upsert with version_id in `deploy_worker.py` | WIRED | None |
| DEP-04 | `rollback_batch()` flag-flip in `deploy_worker.py` | WIRED | None |
| DEP-05 | `DeployLog` written in `run_deploy()`, `force_publish()`, `rollback_batch()` | WIRED | None |
| ALT-01–05 | `alert_worker.py` → `SLOAlertService.notify()` → Telegram/GitHub/Email | WIRED | None |
| QC-01 | `quality_aggregator.py compute_metrics()` reads `market_offers` | WIRED | Overlap with SLO-03 freshness (dual computation, different code paths) |
| QC-02 | `QualityMetric` model persisted via `persist_metrics()` | WIRED | None |
| QC-03 | `quality_aggregator.py --all` iterates all scrapers | WIRED | None |
| QC-04 | `quality_report.py` consumes `quality_metrics` table | WIRED | None |
| QC-05 | `quality-audit.yml` workflow triggers aggregator | WIRED | None |
| QC-06 | `quality-report.yml` workflow triggers report | WIRED | None |

**Requirements with no cross-phase wiring (self-contained):**
- SLO-04 (completeness check) — fully within Phase 06 `slo_validator.py`; not consumed by deploy gate (gate only needs freshness pass)
- SLO-05 (slo_logs queryable) — infrastructure requirement; satisfied by table existence

---

## Summary for Milestone Auditor

**1 broken integration, 1 uncommitted fix.**

The only broken cross-phase wire is SLO-03/DEP-01: `check_freshness()` in `scripts/slo_validator.py` must emit `status='pass'` (not `'skip'`) for the deploy gate to find valid scrapers. The fix is complete in the working tree (9 lines changed) and 6 confirming tests exist in `tests/test_slo_validator.py` (untracked). The fix must be committed and pushed before the nightly deploy pipeline can succeed in production.

**Action required:** Commit `scripts/slo_validator.py`, `tests/test_slo_validator.py`, and `tests/test_deploy_validator.py` from Phase 10 to unblock SLO-03 and DEP-01.

All other cross-phase wiring is intact and verified by static analysis.
