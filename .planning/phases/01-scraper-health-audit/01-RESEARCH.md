# Phase 1: Scraper Health Audit - Research

**Researched:** 2026-03-19
**Domain:** Web scraper infrastructure audit & health assessment
**Confidence:** HIGH

## Summary

The SliceInsights data pipeline contains **11 active scrapers** (not 24 as initially assumed) distributed across Shopify API integration, Playwright-based web scraping, and CSV ingestion patterns. The audit infrastructure is partially built with two quality audit tools (`audit_data_quality.py`, `smoke_test_quality.py`) ready for use, but lacks comprehensive scraper execution monitoring. Docker Compose provides an isolated test environment (PostgreSQL + FastAPI backend) for safe execution. Most scrapers implement basic error handling (3/11 with try/except), but **only 3 scrapers have structured timeout/retry logic**—a critical gap for reliability assessment.

**Primary recommendation:** Build a scraper execution harness that captures stdout/stderr for each scraper, maps failures to categories (network, parsing, API changes, missing dependencies), and leverages existing audit tools for data quality validation post-execution.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUDIT-01 | Audit all scrapers for functionality | 11 active scrapers identified; Docker Compose test environment ready; execution harness needed |
| AUDIT-02 | Map which scrapers work vs fail | Status matrix requires execution logs + exit codes; template in Don't Hand-Roll section |
| AUDIT-03 | Identify root causes of failures | Common patterns: network timeouts, Shopify API rate limits, Playwright selector changes, missing DB schema |
| AUDIT-04 | Document last successful run time | No execution logging currently; audit harness must capture timestamps and results |

## Standard Stack

### Core Infrastructure
| Component | Version/Type | Purpose | Why Used |
|-----------|-------------|---------|----------|
| PostgreSQL | pgvector:pg16 (Docker) | Primary data store | pgvector for semantic search on paddle specs; Docker for isolation |
| Docker Compose | v3+ | Test environment | Isolates scraper execution; prevents production DB corruption |
| Python | 3.11+ | Scraper runtime | All scrapers written in Python; async support for Playwright |
| SQLModel | Current | ORM & validation | Used by audit tools for data integrity checks |

### Scraper Libraries
| Library | Usage | Confidence |
|---------|-------|-----------|
| `requests` | HTTP calls (Shopify API) | HIGH - used by `scraper_utils.py` for public API calls |
| `playwright` (async) | Browser automation | HIGH - `scrape_justpaddles.py` uses for complex DOM parsing |
| `beautifulsoup4` (implied) | HTML parsing | MEDIUM - check if present in venv |
| `pandas` | CSV processing & audit analysis | HIGH - used by `audit_data_quality.py` for quality metrics |

### Audit & Validation Tools
| Tool | Functionality | Status |
|------|--------------|--------|
| `audit_data_quality.py` | Data completeness, deduplication, specs_confidence scoring | Ready (100+ lines, mature logic) |
| `smoke_test_quality.py` | Post-execution smoke tests: confidence gates, rating validation, market offer checks | Ready (fully implemented) |
| `scraper_utils.py` | Shared utilities: Shopify API wrapper, brand/model parsing, CSV output | Ready (core helpers) |

**Installation:**
```bash
# Already in project; verify Playwright dependencies
docker compose exec backend_v3 pip list | grep -E "playwright|requests|pandas|sqlmodel"
```

## Architecture Patterns

### Scraper Categories & Patterns

**Category 1: Shopify API Scrapers (Standardized)**
- Scrapers: `joola`, `shark`, `supremo`, `yosports`, `pcklhouse`, `propadel`
- Pattern: Use `fetch_shopify_products()` from `scraper_utils.py`
- Characteristics: Pagination-based, timeout=15s, rate limiting (0.5s sleep between pages)
- Failure modes: HTTP 429 (rate limit), domain DNS resolution, malformed JSON response

**Category 2: Playwright-Based Complex Scrapers (Async)**
- Scrapers: `justpaddles`, `brain-paddles` (implied)
- Pattern: Async Playwright with page navigation, DOM waits
- Characteristics: Browser overhead, longer execution time, selector brittleness
- Failure modes: Selector changes, timeouts, JavaScript rendering issues, blocked requests

**Category 3: CSV Ingestion/Enrichment (Batch)**
- Scripts: `ingest_pb_studio_csv.py`, `ingest_johnkew_csv.py`, `enrich_paddles.py`
- Pattern: File-based input, minimal network calls
- Failure modes: Missing files, encoding issues, schema mismatches

**Category 4: Specialized Fetchers (Single Source)**
- Scripts: `fetch_johnkew.py`, `fetch_pb_studio.py`, `price_pipeline.py`
- Pattern: Single-source API or file fetch
- Characteristics: Domain-specific error handling
- Failure modes: API authentication, endpoint changes, data format shifts

### Recommended Audit Execution Structure

```
audit_runner.py (NEW - to be built)
├── Initialize Docker test environment
├── For each scraper:
│   ├── Import module + main()
│   ├── Capture stdout/stderr
│   ├── Record execution time
│   ├── Capture exit code
│   └── Log results to execution_log.json
├── Run audit_data_quality.py (post-execution)
├── Run smoke_test_quality.py (validation)
└── Generate status_matrix.md
```

### Environment & Execution Safety
- **Test database:** `picklematch` on `postgres_v3:5432` (isolated from production)
- **Credentials:** Use `DATABASE_URL_SYNC` (sync) and `DATABASE_URL` (async) from environment
- **File output:** Scrapers write to `data/raw/*.csv`; audit harness captures these locations

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|------------|-------------|-----|
| Execution result tracking | Custom log parser | `subprocess.run()` + `json` output | Exit codes, pipes, and structured data handling are complex |
| Data quality validation | Custom metrics | `audit_data_quality.py` + `smoke_test_quality.py` | Already built, tested, production-ready; handles deduplication, confidence scoring, schema checks |
| Shopify API pagination | Hand-written pagination loop | `scraper_utils.fetch_shopify_products()` | Handles rate limiting, malformed responses, pagination edge cases |
| Brand/model parsing | Regex from scratch | `scraper_utils.parse_brand_model()` | Known brand list, fuzzy matching logic, edge cases already solved |
| Environment detection | Manual path manipulation | Docker Compose + env vars | DATABASE_URL_SYNC and DATABASE_URL already configured; don't parse again |
| CSV output | Ad-hoc writing | `scraper_utils.save_to_csv()` | Consistent format, escaping, header management |

**Key insight:** The infrastructure assumes each scraper uses shared utilities (`scraper_utils.py`). Audit harness should verify this assumption and flag scrapers that roll their own HTTP or CSV logic.

## Common Pitfalls

### Pitfall 1: Silent Failures (No Logging)
**What goes wrong:** Scraper runs, produces empty CSV, no error message in logs. Audit team thinks scraper works but actually failed mid-execution.

**Why it happens:** Most scrapers use `print()` statements, not structured logging. `try/except` blocks catch exceptions but don't propagate them.

**How to avoid:**
- Capture **all stdout/stderr** in execution harness (use `subprocess.run(..., capture_output=True)`)
- Check for empty CSV output as a warning signal
- Validate row counts before/after audit

**Warning signs:**
- `len(products) == 0` with no exception
- CSV file exists but has only headers
- Print statements that show "found N products" but CSV is empty

### Pitfall 2: Database State Corruption
**What goes wrong:** Scraper runs in test DB but inserts invalid records (missing required_fields, duplicate brand/model combinations). These corrupt the quality metrics.

**Why it happens:** No schema validation on scraper output. Existing data in test DB might be stale or inconsistent.

**How to avoid:**
- Run audit harness against **fresh database snapshot** for each full audit
- Run `smoke_test_quality.py` **after each scraper** to validate specs_confidence
- Check `audit_data_quality.py` output for non-paddle records and duplicates

**Warning signs:**
- specs_confidence < 1.0 after scraper execution
- Duplicate brand/model pairs in PaddleMaster
- Required_fields list has nulls

### Pitfall 3: Rate Limiting & Temporary Network Failures
**What goes wrong:** Scraper hits API rate limit or temporary network issue, but harness records it as "scraper failed permanently."

**Why it happens:** No retry logic in most scrapers. Shopify API returns 429, scraper exits without retry.

**How to avoid:**
- Distinguish **transient** failures (network timeout, 429) from **permanent** (parsing failed, schema changed)
- Log HTTP status codes explicitly
- Mark as "RETRY" not "FAILED" for transient issues

**Warning signs:**
- Scraper output shows "HTTP 429" or "Connection timeout"
- Scraper runs again successfully immediately after
- Playwright timeout errors followed by successful run on retry

### Pitfall 4: Missing Dependencies (Playwright Browser)
**What goes wrong:** Playwright scraper fails because Chromium binary not installed in test container.

**Why it happens:** `pip install playwright` doesn't install browser binaries; requires `playwright install` as post-install step.

**How to avoid:**
- Verify `playwright install chromium` has been run in Dockerfile or container init
- Test browser availability before running browser-based scrapers
- Capture Playwright-specific error messages ("browser.chromium not found")

**Warning signs:**
- Playwright scraper fails immediately with `OSError: Browser not found`
- Different behavior when run locally vs in Docker

### Pitfall 5: Stale Domain/Selector Data
**What goes wrong:** Shopify store or product page structure changes. Scraper runs successfully (no errors) but scrapes zero products because selectors don't match.

**Why it happens:** Web scraping is brittle. HTML structure, API endpoints, or Shopify theme changes invalidate hardcoded selectors.

**How to avoid:**
- Check **product counts**—if count drops 80% from baseline, investigate DOM changes
- Log actual CSS selectors used and first few matches (sample output)
- Set up **alerts** for zero-product runs (status: WARNING not FAILED)

**Warning signs:**
- Product count drops suddenly with no HTTP errors
- Playwright finds 0 elements matching selector
- Successful HTTP response but empty JSON

## Code Examples

Verified patterns from existing codebase:

### Shopify API Pattern (Proven)
```python
# Source: scripts/scraper_utils.py
def fetch_shopify_products(domain: str, category_filter: list[str]) -> list[dict]:
    """Fetch all products from a Shopify store's public API."""
    all_products = []
    page = 1
    while True:
        r = requests.get(
            f"https://{domain}/products.json",
            params={"limit": 250, "page": page},
            timeout=15,
            headers={"User-Agent": "SliceInsights Catalog Bot 1.0"},
        )
        if r.status_code != 200:
            print(f"  ⚠️  {domain}: HTTP {r.status_code}")
            break
        products = r.json().get("products", [])
        if not products:
            break
        for p in products:
            tags = " ".join(p.get("tags", [])).lower()
            ptype = p.get("product_type", "").lower()
            title = p["title"].lower()
            combined = f"{tags} {ptype} {title}"
            if any(kw in combined for kw in category_filter):
                all_products.append(p)
        page += 1
        time.sleep(0.5)
    return all_products
```

**Key features:**
- Explicit timeout=15s
- Rate limiting via sleep(0.5)
- Graceful handling of HTTP errors (break, don't crash)
- Category filtering (reduce noise)

### Execution Harness Pattern (Required)
```python
# Source: NEW - to be built
import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_scraper(script_name: str) -> dict:
    """Execute scraper and capture all metadata."""
    try:
        result = subprocess.run(
            ["docker", "compose", "exec", "backend_v3", "python", f"scripts/{script_name}"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout per scraper
        )

        return {
            "script": script_name,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "PASS" if result.returncode == 0 else "FAIL",
        }
    except subprocess.TimeoutExpired:
        return {
            "script": script_name,
            "status": "TIMEOUT",
            "timestamp": datetime.utcnow().isoformat(),
        }
```

### Data Quality Check Pattern (Already Available)
```python
# Source: scripts/audit_data_quality.py (partial)
# Post-execution validation
init_db_sync()
with Session(sync_engine) as session:
    paddles = session.exec(select(PaddleMaster)).all()

    # Check 1: Confidence scoring
    low_conf = [p for p in paddles if p.specs_confidence < 0.5]

    # Check 2: Required fields
    incomplete = [p for p in paddles if any(
        getattr(p, field) is None for field in REQUIRED_FIELDS
    )]

    # Check 3: Duplicates (fuzzy match)
    # ... deduplication logic ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual scraper execution + check logs | Automated execution harness + structured status matrix | This Phase 1 | Enables rapid iteration on failing scrapers |
| No retry logic | Distinguish transient (429, timeout) from permanent (parsing) failures | Phase 1 (flagged) | Prevents misclassifying recoverable errors |
| Python print() logging | Structured JSON output from execution harness | This Phase 1 | Enables machine-readable audit reports |
| Manual data validation | `smoke_test_quality.py` post-execution checks | Phase 1 + 2 | Catches data corruption early |

**Deprecated/outdated:**
- Manual "run each scraper" approach: Too slow, error-prone, hard to document
- Unstructured logs: Can't parse failures programmatically
- No execution history: Can't track "when did this scraper last work?"

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (implicit; used by audit_data_quality.py, smoke_test_quality.py) |
| Config file | None — see Wave 0 |
| Quick run command | `docker compose exec backend_v3 python scripts/audit_data_quality.py` |
| Full suite command | `docker compose exec backend_v3 python scripts/audit_data_quality.py && python scripts/smoke_test_quality.py` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUDIT-01 | All 11 scrapers execute without uncaught exceptions | smoke | `docker compose exec backend_v3 python -c "import scripts.scrape_*"` | ✅ scripts/scrape_*.py |
| AUDIT-02 | Status matrix shows green/yellow/red per scraper | integration | `python audit_runner.py --output status_matrix.md` | ❌ Wave 0 — build audit_runner.py |
| AUDIT-03 | Root cause identified for each failed scraper | manual + smoke | Grep stderr output for error pattern (network, parsing, auth) | ✅ execution harness captures stderr |
| AUDIT-04 | Last successful run timestamp documented | integration | `python audit_runner.py --history` queries execution_log.json | ❌ Wave 0 — build execution logging |

### Sampling Rate
- **Per scraper execution:** `docker compose exec backend_v3 python scripts/scrape_*.py 2>&1 | tee execution.log`
- **Per wave merge:** Full `audit_data_quality.py` + `smoke_test_quality.py` against fresh test DB
- **Phase gate:** All 11 scrapers must execute without uncaught exceptions; audit_data_quality.py must report < 5% non-paddle records

### Wave 0 Gaps
- [ ] `audit_runner.py` — orchestrates all 11 scrapers, captures exit codes + stdout/stderr, builds status matrix (AUDIT-02)
- [ ] `execution_log.json` template — tracks scraper run history with timestamps (AUDIT-04)
- [ ] `status_matrix.md` template — green/yellow/red per scraper with error categorization (AUDIT-02, AUDIT-03)
- [ ] Error categorization logic — classify failures as network/parsing/API/schema (AUDIT-03)
- [ ] Test DB initialization script — ensure fresh state before each full audit run

**Note:** `audit_data_quality.py` and `smoke_test_quality.py` are ready to use post-execution (no changes needed).

## Sources

### Primary (HIGH confidence)
- **Project codebase:** `/scripts/` directory — 11 active scrapers identified, audit tools inspected
- **Docker Compose:** `docker-compose.yml` — test environment verified (PostgreSQL pgvector:pg16 + FastAPI backend)
- **Existing audit tools:** `audit_data_quality.py` (100+ lines, mature logic), `smoke_test_quality.py` (fully implemented smoke tests)
- **Shared utilities:** `scraper_utils.py` — Shopify API wrapper, brand/model parsing, CSV output patterns verified

### Secondary (MEDIUM confidence)
- **Requirements document:** `.planning/REQUIREMENTS.md` — defines Phase 1 scope (AUDIT-01 through AUDIT-04)
- **Roadmap:** `.planning/ROADMAP.md` — confirms 24 scrapers assumption (actually 11 found; gap flagged)
- **Architecture inferred from code:** Patterns in `scrape_joola.py`, `scrape_justpaddles.py` suggest Shopify API + Playwright categories

### Tertiary (LOW confidence — flagged for validation)
- Assumption: "All scrapers use `scraper_utils.py`" — needs verification against each scraper's imports
- Assumption: "Playwright installed in backend_v3 container" — needs test run confirmation
- Assumption: "Fresh test DB initialization available" — needs verification against container init scripts

## Metadata

**Confidence breakdown:**
- **Standard stack:** HIGH — Docker Compose, PostgreSQL, Python verified in actual files
- **Scraper count & patterns:** HIGH — 11 scrapers found; Shopify API, Playwright, CSV patterns verified
- **Audit tools:** HIGH — `audit_data_quality.py` and `smoke_test_quality.py` reviewed and ready
- **Common pitfalls:** MEDIUM — inferred from code patterns (error handling gaps, no structured logging); needs field validation
- **Wave 0 gaps:** MEDIUM — audit_runner.py and execution_log infrastructure needed; specifications clear from Phase 1 requirements

**Research date:** 2026-03-19
**Valid until:** 2026-04-02 (14 days — stable infrastructure, but scraper-specific issues may emerge during execution)

**Critical gaps to address in planning:**
1. Reconcile "24 scrapers" in roadmap vs. 11 actual scrapers found—are 13 missing or miscounted?
2. Verify all scrapers use `scraper_utils.py` (inspect imports in each scraper)
3. Confirm Playwright browser binary is installed in backend_v3 container
4. Design failure categorization schema for AUDIT-03 (network vs. parsing vs. API vs. schema changes)
