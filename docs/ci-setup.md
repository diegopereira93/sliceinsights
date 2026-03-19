# CI/CD Setup Guide

This document explains the automated testing pipeline for SliceInsights and how to configure GitHub to enforce CI checks before merging.

## Overview

The CI pipeline runs automatically on every push to `main` and on every pull request targeting `main`. It consists of two jobs:

| Job | What it does | Database required? |
|-----|-------------|-------------------|
| `unit-tests` | Runs pytest suite + ruff linting | No (mocked) |
| `smoke-tests` | Validates data quality against a real DB | Yes (PostgreSQL service) |

**Workflow file:** `.github/workflows/ci.yml`

---

## Branch Protection Setup (Required for CI-04)

Branch protection rules cannot be configured via YAML — they require a one-time setup in GitHub Repository Settings. Follow these steps:

### Step 1: Go to Branch Protection Rules
1. Navigate to your GitHub repository
2. Click **Settings** (top navigation bar)
3. In the left sidebar, click **Branches**
4. Under "Branch protection rules", click **Add rule** (or edit existing rule for `main`)

### Step 2: Configure the Rule
Set the following options:

- **Branch name pattern:** `main`
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: 1 (recommended)
- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - In the search box, type and select: **`unit-tests`**
  - Optionally also add: **`smoke-tests`** (recommended for data integrity)
- ✅ **Do not allow bypassing the above settings** (recommended for enforcement)

### Step 3: Save
Click **Create** (or **Save changes** if editing an existing rule).

### Result
After this setup, any pull request to `main` that fails the `unit-tests` check will be blocked from merging.

---

## Viewing Workflow Logs

1. Go to your GitHub repository
2. Click the **Actions** tab
3. Click on a workflow run to see job details
4. Click on a job (e.g., `unit-tests`) to expand step-by-step logs
5. Failed steps show in red with full stdout/stderr output

### Downloading Logs
In the top-right of the workflow run page, click **...** → **Download log archive** to get a ZIP of all logs.

---

## Troubleshooting Common CI Failures

### `unit-tests` fails: `ModuleNotFoundError`
**Cause:** A new dependency was added to `requirements.txt` or `requirements-dev.txt` but not committed.
**Fix:** Ensure `requirements.txt` and `requirements-dev.txt` are up to date and committed.

### `unit-tests` fails: Playwright browser not found
**Cause:** The Playwright install step failed or chromium binaries weren't cached.
**Fix:** The workflow runs `playwright install chromium && playwright install-deps chromium`. If this fails, check GitHub Actions runner logs for APT errors.

### `smoke-tests` fails: `psycopg2.OperationalError: could not connect to server`
**Cause:** PostgreSQL service container hasn't started in time.
**Fix:** The workflow uses health checks (`pg_isready`). If it still times out, increase `--health-retries` in `ci.yml` from 5 to 10.

### `smoke-tests` fails: `could not open extension control file: vector.control`
**Cause:** pgvector extension wasn't installed in the service container.
**Fix:** Verify the service uses `pgvector/pgvector:pg16` (not the plain `postgres:16` image).

### `smoke-tests` fails: Data quality checks fail
**Cause:** The database was initialized but has no data (smoke tests check active paddle counts).
**Note:** This is **expected behavior** in CI — the smoke tests run against an empty DB. Consider seeding minimal test data if stricter validation is needed (Phase 6 concern).

### Ruff warnings appear but job passes
**Correct behavior.** Ruff is configured with `continue-on-error: true` — it's a fail-warn check. Fix linting issues locally with `ruff check --fix scripts/ app/ tests/`.

---

## Local Development Commands

```bash
# Run unit tests (same as CI)
pytest tests/ -v --ignore=tests/test_e2e_api.py

# Run ruff linting (fail-warn)
ruff check scripts/ app/ tests/ || true

# Run smoke tests (requires docker-compose running)
docker compose exec backend_v3 python scripts/smoke_test_quality.py

# Full local CI simulation
pytest tests/ -v --ignore=tests/test_e2e_api.py && ruff check scripts/ app/ tests/ || true
```

---

## Adding New Tests

1. Add test files to `tests/test_*.py`
2. Follow the mocking pattern in `tests/test_fetchers.py` for scraper tests
3. Follow the mocking pattern in `tests/conftest.py` for API tests
4. Tests that require a real DB should be added to the `smoke-tests` job only (or excluded from CI entirely)

---

*Last updated: 2026-03-19 | Phase 5: CI/CD & Testing*
