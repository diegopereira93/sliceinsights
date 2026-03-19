# Phase 5: CI/CD & Testing — Research

**Researched:** 2026-03-19
**Phase Goal:** Establish automated testing pipeline that validates scrapers on every push to main.

---

## 1. Project Structure Summary

### Scrapers (`scripts/`)
All scrapers follow the `scrape_<store>.py` naming pattern:
- `scrape_brazil_store.py`, `scrape_dropshot_brasil.py`, `scrape_joola.py`
- `scrape_justpaddles.py`, `scrape_pcklhouse.py`, `scrape_propadel.py`
- `scrape_prospin.py`, `scrape_shark.py`, `scrape_supremo.py`, `scrape_yosports.py`
- `scrape_product_specs.py` (generic spec scraper)

Supporting scripts:
- `scraper_utils.py` — shared utilities for scrapers
- `fetch_johnkew.py`, `fetch_pb_studio.py` — data fetchers (Excel/CSV, not web scraping)
- `audit_data_quality.py` — full DB audit (requires DB connection)
- `smoke_test_quality.py` — CI-ready smoke tests (exit 0 = pass, exit 1 = fail, requires DB connection)
- `audit_runner.py`, `autonomous_health_check.py` — automation scripts

### Application (`app/`)
- FastAPI + SQLModel + PostgreSQL (asyncpg async, psycopg2 sync)
- `app/db/database.py` exports `sync_engine`, `init_db_sync` for sync DB ops
- `DATABASE_URL` = async (`postgresql+asyncpg://...`)
- `DATABASE_URL_SYNC` = sync (`postgresql://...`)

---

## 2. Existing Test Coverage

### Framework
- **pytest** (7.4.4) + **pytest-asyncio** (0.23.3)
- Tests in `tests/`, fixtures in `tests/conftest.py`
- All tests use mocked DB sessions (no real DB needed for unit tests)

### Test Files
| File | What it covers | DB Required? |
|---|---|---|
| `test_fetchers.py` | `fetch_johnkew.py`, `fetch_pb_studio.py` logic (fully mocked) | No |
| `test_domain_logic.py` | Paddle domain model calculations | No |
| `test_api_paddles.py` | HTTP endpoints (mocked sessions) | No |
| `test_api_recommendations.py` | Recommendation HTTP endpoints (mocked) | No |
| `test_recommendation_engine.py` | Engine logic (mocked) | No |
| `test_data_quality.py` | Data quality validation functions | No |
| `test_health.py` | `/health` endpoint | No |
| `test_e2e_api.py` | E2E-style API tests | Likely Yes |

### Coverage Gap
- **No unit tests for the 10+ `scrape_*.py` scrapers.** These are the primary deliverable for CI-02.
- `smoke_test_quality.py` requires a real PostgreSQL DB — cannot run in unit test mode.
- `audit_data_quality.py` also requires a real PostgreSQL DB.

---

## 3. CI Infrastructure — Current vs. Needed

### Current State
- **No `.github/` directory exists** — starting from scratch
- Docker Compose uses `pgvector/pgvector:pg16` image
- PostgreSQL config: user=postgres, password=postgres, db=picklematch, internal port 5432

### What Needs to Be Built
1. `.github/workflows/ci.yml` — triggers on push to `main` + PRs to `main`
2. Unit test suite for scrapers (new `tests/test_scrapers.py`)
3. Smoke test integration (as a separate CI job with PostgreSQL service)
4. Branch protection rule documentation (repo settings — cannot be done via CI yaml)

---

## 4. Dependencies & Environment

### Python & Packages
- **Python 3.11** (pinned in Dockerfile, use same in CI)
- CI must install both `requirements.txt` AND `requirements-dev.txt`
- `requirements-dev.txt` includes: `pytest==7.4.4`, `pytest-asyncio==0.23.3`, `ruff==0.1.14`
- **Playwright** (`playwright==1.42.0`) is in `requirements.txt` — scrapers use it
  - Playwright needs browser binaries: `playwright install chromium`
  - In GitHub Actions: also needs `playwright install-deps chromium`

### Database (for smoke tests)
- Use GitHub Actions **service containers**: `pgvector/pgvector:pg16`
- Run as service with: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` env vars
- Connect from workflow step using: `DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/picklematch`
- **Note:** `pgvector` extension must be enabled: `CREATE EXTENSION IF NOT EXISTS vector;`
- `init_db_sync()` in `app/db/database.py` should handle schema creation

### Secrets Needed
- `GROQ_API_KEY` — only for AI features, not needed for scraper CI
- No external secrets needed for unit tests or smoke tests against local DB

---

## 5. Technical Decisions for Planner

### Job Structure (2-job approach)
```
Job 1: unit-tests
  - No DB required
  - Run pytest tests/ (excluding tests that need DB)
  - No Playwright browser install needed (tests are mocked)
  - Include ruff linting (fail-warn: continue-on-error: true)

Job 2: smoke-tests (depends on unit-tests passing)
  - Requires postgresql service container (pgvector/pgvector:pg16)
  - Initialize DB schema
  - Run scripts/smoke_test_quality.py (exit code driven)
```

### Scraper Unit Tests Strategy
- Scrapers use `playwright` for browser automation OR `httpx`/`requests` for HTTP
- Unit tests should mock `playwright` browser context and HTTP calls
- Test: 1) scraper runs without error with mocked responses, 2) output has expected columns
- Focus on `scraper_utils.py` shared functions + 2-3 scraper examples

### Linting (CI-05)
- `ruff==0.1.14` already in `requirements-dev.txt` — no need to install separately
- Mark ruff step as `continue-on-error: true` (fail-warn, not fail-hard)
- Command: `ruff check scripts/ app/ tests/`

### Branch Protection
- Must be configured in GitHub repository Settings > Branches
- Set required status checks: `unit-tests` (and optionally `smoke-tests`)
- This cannot be done via workflow YAML — needs to be documented as manual step or done via GitHub CLI/API

---

## 6. Validation Architecture

**How to validate CI/CD is working after implementation:**

### Checkpoint 1: Workflow File Exists and Valid Syntax
```bash
test -f .github/workflows/ci.yml && echo "PASS: ci.yml exists"
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo "PASS: valid YAML"
```

### Checkpoint 2: Unit Tests Pass Locally
```bash
pip install -r requirements-dev.txt
pytest tests/ -v --ignore=tests/test_e2e_api.py -x
# Expected: all tests pass, exit code 0
```

### Checkpoint 3: Scraper Unit Tests Exist and Pass
```bash
pytest tests/test_scrapers.py -v
# Expected: tests for scraper utilities and at least 2 scrapers pass
```

### Checkpoint 4: Ruff Linting Produces Output (Not Blocking)
```bash
ruff check scripts/ app/ tests/ || true
# Expected: runs without fatal error, warnings are acceptable
```

### Checkpoint 5: Smoke Test Script Structure
```bash
python3 -c "import ast; ast.parse(open('scripts/smoke_test_quality.py').read())" && echo "PASS: smoke_test_quality.py is valid Python"
```

### Checkpoint 6: GitHub Actions Trigger (Post-Push)
- Push a commit to `main` → verify Actions tab shows workflow triggered
- Check that `unit-tests` job runs and passes
- Check that `smoke-tests` job runs after unit-tests

### Checkpoint 7: Branch Protection Active
- Attempt to merge a PR with failing CI → verify merge is blocked
- Create a PR with a test that fails → confirm status check shows as required

---

## 7. Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| Playwright install fails in CI | Medium | Use `playwright install-deps chromium` + separate step |
| pgvector extension not available in service container | Low | `pgvector/pgvector:pg16` image includes it by default |
| `init_db_sync()` creates tables but doesn't install pgvector | Medium | Add `CREATE EXTENSION IF NOT EXISTS vector` SQL step before init |
| Smoke tests take too long (full DB audit) | Low | `smoke_test_quality.py` only queries, doesn't scrape — should be fast |
| Branch protection requires specific GitHub permissions | Medium | Document clearly as manual step for repo admin |
| E2E tests (`test_e2e_api.py`) fail in CI without DB | High | Exclude from unit-test job; run separately or skip in Phase 5 |

---

## 8. Phase Boundary

### In Scope (Phase 5)
- `.github/workflows/ci.yml` with 2 jobs (unit-tests, smoke-tests)
- New `tests/test_scrapers.py` with mocked scraper unit tests
- Ruff linting step (fail-warn)
- Documentation for branch protection setup
- `requirements-dev.txt` verified and complete for CI

### Out of Scope (Phase 5)
- Actual deployment pipeline (Phase 8)
- Monitoring/alerting (Phase 7)
- SLO enforcement (Phase 6)
- Container registry / Docker publishing
- Running scrapers in CI (they need external sites — too flaky)
- E2E tests against production DB

---

## RESEARCH COMPLETE
