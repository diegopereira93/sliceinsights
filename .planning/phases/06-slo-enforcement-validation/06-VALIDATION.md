---
phase: 6
slug: slo-enforcement-validation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (existing `tests/` suite) |
| **Config file** | `pytest.ini` or `pyproject.toml` (existing) |
| **Quick run command** | `pytest tests/test_slo_validator.py -v` |
| **Full suite command** | `pytest tests/ -v --ignore=tests/test_e2e_api.py` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_slo_validator.py -v`
- **After every plan wave:** Run `pytest tests/ -v --ignore=tests/test_e2e_api.py`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 6-01-01 | 01 | 1 | SLO-03, SLO-04 | unit | `pytest tests/test_slo_validator.py::test_check_freshness -v` | ⬜ pending |
| 6-01-02 | 01 | 1 | SLO-05 | unit | `pytest tests/test_slo_validator.py::test_slo_log_written -v` | ⬜ pending |
| 6-02-01 | 02 | 1 | SLO-01 | manual | Run scraper, check `slo_logs` table for new row | ⬜ pending |
| 6-02-02 | 02 | 1 | SLO-01, SLO-05 | db-query | `psql $DATABASE_URL_SYNC -c "SELECT * FROM slo_logs ORDER BY checked_at DESC LIMIT 5;"` | ⬜ pending |
| 6-03-01 | 03 | 2 | SLO-02 | manual | Trigger `slo-check.yml` via GitHub Actions → Actions tab → Run workflow | ⬜ pending |
| 6-03-02 | 03 | 2 | SLO-05 | db-query | `psql $DATABASE_URL_SYNC -c "SELECT scraper_name, status FROM slo_logs WHERE status='fail';"` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_slo_validator.py` — stubs for SLO-01 through SLO-05 validation logic
- [ ] `tests/conftest.py` — extend with SLO fixtures (mock session, threshold constants)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Scheduled workflow runs every 6h | SLO-02 | Cannot automate cron scheduling locally | Go to GitHub → Actions → SLO Check → Run workflow manually; verify job completes with exit 0 |
| Real-time hook triggers post-scraper | SLO-01 | Requires live scraper run with DB access | Run a scraper script; query `SELECT COUNT(*) FROM slo_logs WHERE checked_at > NOW() - INTERVAL '1 minute'` — expect ≥ 1 |
| Breach detection within 1 hour | SLO-03/04 | Requires simulated stale data | `UPDATE market_offers SET updated_at = NOW() - INTERVAL '25 hours' WHERE id = 1;` then `python scripts/slo_validator.py --all` → expect `fail` row in slo_logs |

---

## Validation Sign-Off

- [ ] All tasks have `automated` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
