---
phase: 12
slug: spec-enrichment-scrapers
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` or `pyproject.toml` |
| **Quick run command** | `pytest tests/ -x -q --tb=short` |
| **Full suite command** | `pytest tests/ -q --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q --tb=short`
- **After every plan wave:** Run `pytest tests/ -q --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-W0-migration | 01 | 0 | SCRP-03/05 | unit | `pytest tests/test_models.py -x -q` | ❌ W0 | ⬜ pending |
| 12-W0-enricher-stub | 01 | 0 | SCRP-03/04/05 | unit | `pytest tests/test_spec_enricher.py -x -q` | ❌ W0 | ⬜ pending |
| 12-01-enricher-core | 01 | 1 | SCRP-03/04/05 | unit | `pytest tests/test_spec_enricher.py -x -q` | ❌ W0 | ⬜ pending |
| 12-01-per-store | 01 | 1 | SCRP-02 | unit | `pytest tests/test_spec_enricher.py::test_store_extractors -x -q` | ❌ W0 | ⬜ pending |
| 12-02-archive-enrichment | 02 | 1 | SCRP-03 | unit | `pytest tests/ -x -q` (full suite green) | ✅ | ⬜ pending |
| 12-02-workflow | 02 | 2 | SCRP-02/06 | manual | verify `.github/workflows/scraper-weekly.yml` triggers correctly | ✅ | ⬜ pending |
| 12-02-quality-audit | 02 | 2 | SCRP-06 | manual | run quality audit, check spec completeness ≥ 70% | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_spec_enricher.py` — stubs for SCRP-02, SCRP-03, SCRP-04, SCRP-05: `test_4_fields_required`, `test_partial_specs_not_saved`, `test_source_recorded_in_validation_sources`, `test_store_extractors` (one per store)
- [ ] `tests/conftest.py` — fixtures: in-memory DB session, mock paddle rows, mock HTML responses per store
- [ ] `tests/test_models.py` — test `weight_grams` column exists on `paddle_master` after migration

*Existing pytest infrastructure detected — no new framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Weekly cron triggers all 10 scrapers in GHA | SCRP-02 | Requires live GHA run | Trigger `scraper-weekly.yml` via `workflow_dispatch`; verify all 10 jobs appear |
| Spec completeness ≥ 70% after cycle | SCRP-06 | Requires live DB + full scrape cycle | Run quality audit tool; check `paddle_master` completeness metric |
| Playwright scrapers work headless in CI | SCRP-02 | Requires CI environment | Check GHA run logs for 4 Playwright stores (joola, brazilpickleballstore, drop_shot_brasil, just_paddles) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
