---
phase: 1
slug: scraper-health-audit
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (implicit; used by audit_data_quality.py, smoke_test_quality.py) |
| **Config file** | None — see Wave 0 |
| **Quick run command** | `docker compose exec backend_v3 python scripts/audit_data_quality.py` |
| **Full suite command** | `docker compose exec backend_v3 python scripts/audit_data_quality.py && python scripts/smoke_test_quality.py` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker compose exec backend_v3 python scripts/audit_data_quality.py`
- **After every plan wave:** Run full `audit_data_quality.py` + `smoke_test_quality.py` against fresh test DB
- **Before `/gsd:verify-work`:** All 11 scrapers must execute without uncaught exceptions; audit_data_quality.py must report < 5% non-paddle records
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | AUDIT-03 | unit | `python -m pytest .audit/tests/test_error_categorization.py -v` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | AUDIT-01 | integration | `docker compose exec backend_v3 python scripts/audit_runner.py --dry-run` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | AUDIT-01, AUDIT-02 | integration | `docker compose exec backend_v3 python scripts/audit_runner.py && grep -c "status" .audit/status_matrix.md` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 2 | AUDIT-03 | integration | `python -c "import json; data=json.load(open('.audit/root_cause_analysis.json')); assert len(data['failures']) > 0"` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 2 | AUDIT-02, AUDIT-03 | integration | `grep -E "^\|.*\|.*\|" .audit/detailed_audit_report.md \| wc -l` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 2 | AUDIT-04 | integration | `python -c "import json; data=json.load(open('.audit/scraper_health_summary.json')); assert 'timestamps' in data"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.audit/tests/test_error_categorization.py` — unit tests for 9 error categories
- [ ] `.audit/tests/conftest.py` — shared fixtures for test DB, audit_runner mock
- [ ] `.audit/audit_runner_test.py` — integration tests for scraper orchestration and output format validation
- [ ] `scripts/test_db_init.py` — reset test DB to fresh state before full audit run

**Note:** `audit_data_quality.py` and `smoke_test_quality.py` are ready to use post-execution (no changes needed).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Root cause categorization accuracy | AUDIT-03 | Requires domain knowledge of actual failure patterns in web scrapers | Review .audit/detailed_audit_report.md; verify each failure reason matches observed error (network timeout, parsing error, auth failure, etc.) |
| Production safety recommendation | AUDIT-01 | Requires judgment on acceptable failure modes and retry strategy | Check .audit/scraper_health_summary.json for "production_ready" field; verify GREEN scrapers have < 2% failure rate |
| Recommendations prioritization | AUDIT-03 | Requires prioritization across scope/impact | Review .audit/detailed_audit_report.md "Recommendations" section; verify quick fixes listed before refactoring work |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify commands or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all ❌ references in verification map
- [ ] No watch-mode flags in test commands
- [ ] Feedback latency < 120s per wave
- [ ] `nyquist_compliant: true` set in frontmatter after Wave 0 is complete

**Approval:** pending — Wave 0 infrastructure must be built during plan execution

---

*Phase: 01-scraper-health-audit*
*Validation created: 2026-03-19 — from research Validation Architecture*
