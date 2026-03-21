---
phase: 11
slug: seed-cleanup-store-catalog
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | STORE-01 | migration | `alembic upgrade head` | ✅ | ⬜ pending |
| 11-01-02 | 01 | 1 | STORE-01 | unit | `pytest tests/test_store_model.py -x -q` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 1 | STORE-02 | unit | `pytest tests/test_ingestor.py -x -q` | ✅ | ⬜ pending |
| 11-02-02 | 02 | 1 | SCRP-01 | integration | `pytest tests/test_pipeline_no_csv.py -x -q` | ✅ | ⬜ pending |
| 11-03-01 | 03 | 2 | SCRP-01 | integration | `pytest tests/test_pipeline_no_csv.py -x -q` | ✅ | ⬜ pending |
| 11-03-02 | 03 | 2 | STORE-02 | unit | `pytest tests/ -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_store_model.py` — unit tests for Store model attributes (name, base_url, active, brands)

*Existing infrastructure (`tests/test_ingestor.py`, `tests/test_pipeline_no_csv.py`) covers most phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| justpaddles market offers scraped | SCRP-01 | Requires live network access | Run `python scripts/run_scraper.py justpaddles`; verify `market_offers` has rows with non-null `store_id` and `product_url` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
