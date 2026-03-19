---
phase: 05-ci-cd-and-testing
plan: "01"
subsystem: ci-cd
tags: [github-actions, pytest, ruff, pgvector, smoke-tests]
dependency_graph:
  requires: []
  provides: [ci-workflow, unit-test-job, smoke-test-job]
  affects: [05-02, 05-03]
tech_stack:
  added: [github-actions, pgvector/pgvector:pg16]
  patterns: [fail-warn-linting, service-containers, job-dependencies]
key_files:
  created:
    - .github/workflows/ci.yml
  modified: []
decisions:
  - "Ruff runs with continue-on-error: true (fail-warn) — linting never blocks merges in Phase 5"
  - "smoke-tests uses needs: unit-tests — smoke tests are skipped entirely if unit tests fail"
  - "pgvector extension enabled via PGPASSWORD psql inline command before schema init"
  - "Playwright install-deps included for Linux CI system dependencies"
metrics:
  duration_minutes: 5
  completed_date: "2026-03-19"
  tasks_completed: 1
  tasks_total: 1
  files_created: 1
  files_modified: 0
---

# Phase 05 Plan 01: GitHub Actions CI Workflow Summary

**One-liner:** GitHub Actions CI with two-job pipeline — pytest unit tests + pgvector smoke tests using `pgvector/pgvector:pg16` service container.

## What Was Built

`.github/workflows/ci.yml` — a two-job CI workflow that triggers on push/PR to main.

**Job 1: `unit-tests`**
- Runs on `ubuntu-latest` with Python 3.11
- Installs `requirements.txt` + `requirements-dev.txt` (pytest 7.4.4, ruff 0.1.14)
- Runs `pytest tests/ -v --ignore=tests/test_e2e_api.py`
- Ruff linting runs as a fail-warn step (`continue-on-error: true`)

**Job 2: `smoke-tests`**
- Depends on `unit-tests` via `needs: unit-tests`
- Spins up a `pgvector/pgvector:pg16` PostgreSQL service container with health checks
- Enables the `vector` extension via inline psql
- Initializes schema via `init_db_sync()`
- Runs `python scripts/smoke_test_quality.py` (exit 0 = pass, exit 1 = fail)

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| `continue-on-error: true` on ruff | Satisfies CI-05: linting is advisory, not blocking |
| `needs: unit-tests` on smoke-tests | Satisfies CI-04: smoke tests skipped on unit test failure |
| `pgvector/pgvector:pg16` service | Matches development Docker image exactly |
| `cache: 'pip'` on both jobs | Speeds up subsequent runs |
| Playwright `install-deps chromium` | Required for Linux runner system dependencies |

## Deviations from Plan

None - plan executed exactly as written.

## Verification

All 12 acceptance criteria passed:
- YAML syntactically valid
- Triggers on push and pull_request to main
- Both `unit-tests` and `smoke-tests` jobs present
- `needs: unit-tests` dependency enforced
- `continue-on-error: true` on ruff step
- `pgvector/pgvector:pg16` image used
- Python 3.11 configured
- `pytest tests/` present
- `smoke_test_quality.py` invoked

## Commits

| Task | Description | Hash |
|------|-------------|------|
| 1 | Create GitHub Actions CI/CD workflow | 3e8307d |

## Self-Check: PASSED
