---
phase: 5
slug: ci-cd-and-testing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4.4 + pytest-asyncio 0.23.3 |
| **Config file** | `requirements-dev.txt` (already exists) |
| **Quick run command** | `pytest tests/ -x -q --ignore=tests/test_e2e_api.py` |
| **Full suite command** | `pytest tests/ -v --ignore=tests/test_e2e_api.py` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q --ignore=tests/test_e2e_api.py`
- **After every plan wave:** Run `pytest tests/ -v --ignore=tests/test_e2e_api.py && ruff check scripts/ app/ tests/ || true`
- **Before `/gsd-verify-work`:** Full suite must be green + ci.yml must exist + ruff must run
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| CI workflow creation | 01 | 1 | CI-01 | file-check | `test -f .github/workflows/ci.yml` | ⬜ pending |
| Unit test job | 01 | 1 | CI-02 | yaml-check | `grep -q "pytest" .github/workflows/ci.yml` | ⬜ pending |
| Smoke test job | 01 | 1 | CI-03 | yaml-check | `grep -q "smoke_test_quality" .github/workflows/ci.yml` | ⬜ pending |
| Ruff linting | 01 | 1 | CI-05 | yaml-check | `grep -q "ruff" .github/workflows/ci.yml` | ⬜ pending |
| Scraper unit tests | 02 | 2 | CI-02 | unit | `pytest tests/test_scrapers.py -v` | ⬜ pending |
| Branch protection docs | 03 | 2 | CI-04 | file-check | `test -f docs/CI.md` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_scrapers.py` — stubs for scraper unit tests (CI-02)
- Existing `tests/conftest.py` covers shared fixtures — no changes needed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Push to main triggers CI | CI-01 | Requires real GitHub push + Actions | Push a commit to main, check Actions tab shows workflow triggered |
| Branch protection blocks bad PRs | CI-04 | Requires repo admin access | Create PR with failing test, verify merge is blocked |
| Merge requires CI pass | CI-04 | Requires repo settings | Check Settings > Branches > branch protection rules include CI |
