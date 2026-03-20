# Phase 9: Data Quality Checks & Reporting - Research

**Researched:** 2026-03-20
**Domain:** Data quality monitoring, GitHub Actions matrix workflows, FastAPI caching, HTML email reports
**Confidence:** HIGH

## Summary

Phase 9 closes the last remaining v2.0 requirement group (QC-01..QC-06). The foundation is entirely in place: SLOLog's SQLModel+JSONB pattern is the direct template for the new `quality_metrics` table; `SLOAlertService.send_email()` is the transport layer for the weekly report; and the slo-check.yml matrix/cron/workflow_dispatch pattern is the exact skeleton for `quality-audit.yml`. The codebase has `cachetools.TTLCache` already imported in `routes.py` and used for `_brands_cache` — that same pattern works for the 5-minute dashboard cache.

The three new files with real logic are `scripts/quality_aggregator.py` (metric calculation + DB persistence), `app/api/endpoints/quality.py` (dashboard endpoint), and `scripts/quality_report.py` (weekly trend report). A new Alembic migration adds `quality_metrics`. Two GitHub Actions workflows orchestrate the schedule. All patterns are proven in prior phases — no new libraries are required.

**Primary recommendation:** Model everything after slo-check.yml + SLOLog + routes.py TTLCache. Write `quality_aggregator.py` as the single source of metric truth (freshness, completeness_pct, coverage_pct, product_count, error_rate); the dashboard endpoint is a read-only view over the most recent row per scraper.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Data Model (quality_metrics)**
- New table `quality_metrics` — separate from `slo_logs`
- 5 metrics per scraper per run: `freshness_hours`, `completeness_pct`, `coverage_pct`, `product_count`, `error_rate`
- Granularity: one row per scraper per workflow execution (not hourly aggregate)
- Field `run_id` required — correlates with GitHub Actions run number
- Retention: indefinite (no auto-purge for now)

**Dashboard Endpoint**
- Route: `GET /api/quality/dashboard` — consistent with existing `app/api/routes.py` pattern
- Public endpoint, no authentication
- Returns latest snapshot per scraper (not history)
- Global status: `healthy` (all pass) / `degraded` (1-2 failing) / `critical` (3+ failing)
- In-memory cache: 5 minutes
- Exact JSON shape approved (see CONTEXT.md Dashboard Endpoint section)

**Weekly Report**
- Format: HTML email — reuse `SLOAlertService` from Phase 7
- Channel: email only — same `admin_email_group` already configured
- Schedule: Monday 08:00 UTC (`cron: '0 8 * * 1'`), covering previous week
- Anomaly definition: > 10% drop in any metric vs prior week
- Trend: HTML table with 4 weeks of data + up/down arrows, no matplotlib
- Email structure: separate "Improving" (green) and "Degrading" (red) sections

**Hourly Audit Integration**
- New `scripts/quality_aggregator.py` — do NOT modify `scripts/audit_data_quality.py`
- Workflow `quality-audit.yml`: matrix strategy, one job per scraper in parallel
- Consolidation job after matrix completes: saves global record with run_id + aggregated status
- `run_id` injected via `GITHUB_RUN_ID` env var in each parallel job
- Triggers: `schedule` (hourly cron) + `workflow_dispatch`
- Individual scraper failures: persist to DB only, no immediate alerts

### Claude's Discretion
- Exact schema of `quality_metrics` table (column types, indexes)
- Logic for computing `coverage_pct` per product (which fields to count)
- In-memory cache implementation (plain dict vs `cachetools.TTLCache` vs `functools.lru_cache`)
- HTML email template (colors, layout)
- `error_rate` calculation method (window: last 24h)

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QC-01 | Hourly data quality audit job runs for all 11 active scrapers | GitHub Actions matrix pattern from slo-check.yml; `cron: '0 * * * *'` schedule |
| QC-02 | Audit measures: freshness, completeness, coverage per scraper | `audit_data_quality.py` has freshness + field coverage logic to extract as reference; `slo_validator.py` has freshness calculation |
| QC-03 | Metrics stored in database for historical trending | SQLModel+JSONB pattern from `SLOLog`; new Alembic migration required |
| QC-04 | Quality dashboard endpoint (HTTP GET) returns current metrics as JSON | FastAPI route in `routes.py`; `cachetools.TTLCache` already imported and used |
| QC-05 | Weekly quality report generated showing trends and anomalies | `SLOAlertService.send_email()` as transport; pandas for 4-week aggregation; `quality-report.yml` workflow |
| QC-06 | Report highlights which scrapers are degrading or improving | pandas week-over-week delta; > 10% drop = anomaly; HTML table with arrows |
</phase_requirements>

---

## Standard Stack

### Core (all already in requirements.txt or the codebase)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLModel | pinned in requirements.txt | ORM model for `quality_metrics` | Same pattern as `SLOLog`, `SLOAlert`, `DeployLog` |
| SQLAlchemy (JSONB) | transitive dep | `details` JSONB column for extras | Established pattern in `SLOLog.details` |
| pandas | 2.2.0 | 4-week trend aggregation, week-over-week delta | Already in requirements.txt |
| cachetools | installed (used in routes.py) | `TTLCache` for 5-min dashboard cache | Already imported in `app/api/routes.py` |
| FastAPI | pinned | Dashboard endpoint registration | Existing API server |
| Alembic | pinned | Migration for `quality_metrics` table | Established migration workflow |
| smtplib (stdlib) | stdlib | Email transport | Used by `SLOAlertService._send_email()` |

### No New Dependencies Required

Phase 9 introduces zero new packages. All needed libraries are present. Confirm with:
```bash
pip show cachetools pandas sqlmodel alembic
```

---

## Architecture Patterns

### Recommended File Structure (new files only)

```
scripts/
└── quality_aggregator.py    # CLI: compute + persist metrics for one or all scrapers
└── quality_report.py        # CLI: generate + email weekly trend report

app/
└── models/
    └── quality_metric.py    # QualityMetric SQLModel (mirrors slo.py structure)
└── api/
    └── endpoints/
        └── quality.py       # GET /api/quality/dashboard router

.github/workflows/
└── quality-audit.yml        # Hourly matrix job (one job per scraper)
└── quality-report.yml       # Monday 08:00 UTC weekly report
```

### Pattern 1: QualityMetric Model (mirrors SLOLog)

```python
# Source: app/models/slo.py — same pattern
from typing import Optional, Dict
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB

class QualityMetric(SQLModel, table=True):
    __tablename__ = "quality_metrics"

    id: Optional[int] = Field(default=None, primary_key=True)
    scraper_name: str = Field(index=True)
    run_id: str = Field(index=True)          # GITHUB_RUN_ID for incident correlation
    freshness_hours: float
    completeness_pct: float                  # % products with all required fields filled
    coverage_pct: float                      # % required fields filled across all products
    product_count: int
    error_rate: float                        # fraction of runs in last 24h that failed
    status: str                              # "pass" | "fail"
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    details: Dict = Field(default={}, sa_column=Column(JSONB))
```

**Index recommendation (Claude's discretion):** Composite index on `(scraper_name, checked_at DESC)` — dashboard query always fetches latest row per scraper.

### Pattern 2: quality_aggregator.py CLI

```python
# Source: scripts/run_scraper.py and scripts/slo_validator.py — same entry-point pattern
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scraper", help="Single scraper name")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    run_id = os.getenv("GITHUB_RUN_ID", "manual")
    if args.all:
        for name in ACTIVE_SCRAPERS:
            compute_and_persist(name, run_id)
    elif args.scraper:
        compute_and_persist(args.scraper, run_id)
```

### Pattern 3: GitHub Actions Matrix (quality-audit.yml)

```yaml
# Source: slo-check.yml — cron + workflow_dispatch skeleton
on:
  schedule:
    - cron: '0 * * * *'   # Every hour
  workflow_dispatch: {}

jobs:
  audit:
    name: Quality Audit (${{ matrix.scraper }})
    runs-on: ubuntu-latest
    continue-on-error: true
    strategy:
      matrix:
        scraper: [mercado_livre, amazon_br, netshoes, ...]  # all 11
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11', cache: 'pip' }
      - run: pip install -r requirements.txt
      - run: python scripts/quality_aggregator.py --scraper ${{ matrix.scraper }}
        env:
          DATABASE_URL_SYNC: ${{ secrets.DATABASE_URL_SYNC }}
          GITHUB_RUN_ID: ${{ github.run_id }}

  consolidate:
    name: Consolidate Results
    needs: audit
    if: always()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11', cache: 'pip' }
      - run: pip install -r requirements.txt
      - run: python scripts/quality_aggregator.py --consolidate
        env:
          DATABASE_URL_SYNC: ${{ secrets.DATABASE_URL_SYNC }}
          GITHUB_RUN_ID: ${{ github.run_id }}
```

### Pattern 4: Dashboard Endpoint with TTLCache

```python
# Source: app/api/routes.py _brands_cache pattern
from cachetools import TTLCache

_quality_cache = TTLCache(maxsize=1, ttl=300)  # 5 min — matches hourly update cadence

@router.get("/quality/dashboard")
async def quality_dashboard(session: AsyncSession = Depends(get_session)):
    if "data" in _quality_cache:
        return _quality_cache["data"]

    # Query: latest row per scraper (window function or GROUP BY + subquery)
    # ... build response ...
    _quality_cache["data"] = response
    return response
```

**SQL pattern for latest-per-scraper (< 500ms requirement):**
```sql
-- Source: standard PostgreSQL pattern, verified against project's SQLAlchemy usage
SELECT DISTINCT ON (scraper_name) *
FROM quality_metrics
ORDER BY scraper_name, checked_at DESC;
```

### Pattern 5: Weekly Report — pandas week-over-week delta

```python
# pandas 2.2 — already in requirements.txt
df = pd.DataFrame(rows)                          # rows from quality_metrics last 4 weeks
df['week'] = pd.to_datetime(df['checked_at']).dt.isocalendar().week
weekly = df.groupby(['scraper_name', 'week']).mean(numeric_only=True)

# Anomaly: > 10% drop in any metric vs prior week (locked decision)
current = weekly.xs(current_week, level='week')
prior   = weekly.xs(prior_week, level='week')
delta   = (current - prior) / prior.abs()
degrading = delta[delta.min(axis=1) < -0.10].index.tolist()
improving = delta[delta.max(axis=1) > 0.10].index.tolist()
```

### Pattern 6: Send HTML Report via SLOAlertService

```python
# Source: app/services/slo_alerts.py — _send_email() uses EmailMessage
# For HTML: extend _send_email to accept html_body parameter and call msg.add_alternative()
msg = EmailMessage()
msg["Subject"] = f"[SliceInsights] Weekly Quality Report — Week {week_number}"
msg["From"] = self.email_user
msg["To"] = ", ".join(recipients)
msg.set_content(plain_text_fallback)
msg.add_alternative(html_body, subtype="html")
```

The weekly report sender can either extend `SLOAlertService` with a `send_report()` method, or be a standalone function in `scripts/quality_report.py` that imports the email config helpers. Standalone is simpler and avoids coupling a script to the service class.

### Pattern 7: Register Dashboard Router in routes.py

```python
# Source: app/api/routes.py line 529 — include_router pattern
from app.api.endpoints.quality import router as quality_router
router.include_router(quality_router, prefix="/quality", tags=["quality"])
```

Alternatively, register the endpoint directly in `routes.py` to match the existing flat pattern (all current endpoints are in the single `routes.py` file). Either approach works — the flat approach is simpler given the single endpoint.

### Anti-Patterns to Avoid

- **Modifying `audit_data_quality.py`:** It is a manual audit tool with print-heavy output, not designed for automated metric persistence. The locked decision is to leave it untouched.
- **Storing aggregated hourly metrics:** The locked decision is one row per scraper per workflow execution. Do not pre-aggregate.
- **Blocking the hourly matrix on consolidation:** Use `if: always()` on the consolidate job so individual scraper failures don't prevent the global record from being written.
- **Using matplotlib for the report:** Locked decision is HTML table with arrows — no chart generation.
- **Async session in quality_aggregator.py:** The script runs outside FastAPI, so use `sync_engine` with `Session(sync_engine)` — same as `audit_data_quality.py` and `slo_validator.py`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 5-min dashboard cache | Custom dict + timestamp logic | `cachetools.TTLCache(maxsize=1, ttl=300)` | Already imported in routes.py; thread-safe TTL built in |
| Email transport | Custom SMTP wrapper | `SLOAlertService` + stdlib `smtplib` | Already tested; handles TLS, recipients, credentials |
| Week-over-week aggregation | Manual SQL pivot | pandas `groupby + mean + delta` | pandas 2.2 already in requirements.txt; tested pattern |
| DB migration | Manual SQL DDL | Alembic `autogenerate` | Existing migration workflow in `alembic/` |
| Latest-row-per-group query | Application-level loop | PostgreSQL `DISTINCT ON` | Single query, uses index on `(scraper_name, checked_at)` |

---

## Common Pitfalls

### Pitfall 1: Matrix Job Secrets Not Propagated
**What goes wrong:** Matrix jobs each need `DATABASE_URL_SYNC` and `GITHUB_RUN_ID`. If `env:` is placed at workflow level instead of step level, some Actions runners may not inherit them.
**Why it happens:** GitHub Actions env scoping — workflow-level env is inherited, but `secrets` must be explicitly mapped.
**How to avoid:** Inject both `DATABASE_URL_SYNC: ${{ secrets.DATABASE_URL_SYNC }}` and `GITHUB_RUN_ID: ${{ github.run_id }}` in the `env:` block of the run step (not just the job), matching the pattern in `slo-check.yml`.
**Warning signs:** `KeyError: DATABASE_URL_SYNC` in aggregator logs; `run_id = None` in persisted rows.

### Pitfall 2: Dashboard Query Performance (< 500ms requirement)
**What goes wrong:** Without an index on `(scraper_name, checked_at)`, the "latest row per scraper" query does a sequential scan that grows with retention. With indefinite retention (locked decision), this becomes a problem.
**Why it happens:** `DISTINCT ON` and `GROUP BY` both need an ordered scan of the relevant partition.
**How to avoid:** Add `Index("ix_quality_metrics_scraper_checked", "scraper_name", "checked_at")` to the model. The 5-minute TTLCache means the query runs at most once per 5 minutes regardless.
**Warning signs:** Dashboard response > 500ms in staging; `EXPLAIN` shows Seq Scan on quality_metrics.

### Pitfall 3: Week Boundary Edge Case in Trend Calculation
**What goes wrong:** If the report runs at Monday 08:00 UTC and the aggregator ran for the first time on the same Monday before 08:00, the "current week" in pandas' ISO week may already include that day, shifting the 4-week window.
**Why it happens:** ISO week starts Monday — the report schedule and week boundary coincide.
**How to avoid:** Calculate the reporting window as "rows WHERE checked_at < Monday 08:00 UTC of the report run date" and group by floor-division to ISO week. Explicitly pass a `reference_date` to the report generator for testability.
**Warning signs:** Week 1 in the report always shows only a few hours of data; trend arrows flip unexpectedly.

### Pitfall 4: Alembic Import Registration
**What goes wrong:** New `QualityMetric` model will not appear in `alembic autogenerate` unless imported into `alembic/env.py` and `app/db/database.py`.
**Why it happens:** SQLModel metadata only includes tables whose model classes have been imported. See `database.py` lines importing `SLOLog`, `SLOAlert`, `DeployLog` — each was added explicitly.
**How to avoid:** Add `from app.models.quality_metric import QualityMetric  # noqa: F401` to both `database.py` and `alembic/env.py`. Verify with `alembic check` before committing the migration.
**Warning signs:** `alembic autogenerate` produces empty migration; `quality_metrics` table not created in production.

### Pitfall 5: error_rate Window Ambiguity
**What goes wrong:** `error_rate` is Claude's discretion (locked: last 24h window). If the aggregator is called per-scraper in parallel and one job starts at 00:59 and another at 01:01, the 24h window start differs by 2 minutes, creating inconsistent error_rate values for the same run_id.
**Why it happens:** Wall-clock 24h lookback computed independently in each parallel job.
**How to avoid:** Define the 24h window as `NOW() - interval '24 hours'` anchored to the `checked_at` of the current row, not the process start time. Since runs are at most 1-2 minutes apart within a matrix, the difference is negligible. Document this as a known limitation.

---

## Code Examples

### Register QualityMetric in database.py

```python
# Source: app/db/database.py — existing pattern (lines 9-10)
from app.models.quality_metric import QualityMetric  # noqa: F401 — registers with SQLModel metadata
```

### Alembic Migration Command

```bash
# Source: established project workflow (same as 08-01, 06-01)
alembic revision --autogenerate -m "add_quality_metrics_table"
alembic upgrade head
```

### Dashboard Response Construction (SQLAlchemy DISTINCT ON)

```python
from sqlalchemy import text

async def get_latest_metrics(session: AsyncSession) -> list[dict]:
    result = await session.execute(text("""
        SELECT DISTINCT ON (scraper_name)
            scraper_name, freshness_hours, completeness_pct,
            coverage_pct, product_count, error_rate, status, checked_at
        FROM quality_metrics
        ORDER BY scraper_name, checked_at DESC
    """))
    return [dict(row._mapping) for row in result]
```

### Metric Status Classification

```python
# Claude's discretion — proposed thresholds matching SLO tier logic
def classify_scraper_status(m: QualityMetric) -> str:
    if m.freshness_hours > 24 or m.completeness_pct < 70 or m.error_rate > 0.3:
        return "fail"
    return "pass"

def classify_global_status(scrapers: list[dict]) -> str:
    failing = sum(1 for s in scrapers if s["status"] == "fail")
    if failing == 0:
        return "healthy"
    elif failing <= 2:
        return "degraded"
    return "critical"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Print-only audit (`audit_data_quality.py`) | Persisted metrics in `quality_metrics` table | Phase 9 | Enables historical trending and dashboard |
| Manual audit runs | Hourly automated matrix job | Phase 9 | Continuous monitoring without human intervention |
| No quality dashboard | `GET /api/quality/dashboard` endpoint | Phase 9 | Programmatic health check integration |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, all phases use it) |
| Config file | None — runs with `pytest tests/` |
| Quick run command | `pytest tests/test_quality_aggregator.py tests/test_quality_dashboard.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QC-01 | quality-audit.yml triggers and runs all 11 scrapers | manual (workflow) | n/a — GitHub Actions | N/A |
| QC-02 | `compute_metrics()` returns freshness, completeness, coverage, product_count, error_rate | unit | `pytest tests/test_quality_aggregator.py -x` | Wave 0 |
| QC-03 | `persist_metrics()` inserts a row; row queryable after insert | unit | `pytest tests/test_quality_aggregator.py::test_persist_metrics -x` | Wave 0 |
| QC-04 | `GET /api/quality/dashboard` returns 200, correct JSON shape, < 500ms | unit | `pytest tests/test_quality_dashboard.py -x` | Wave 0 |
| QC-05 | `build_weekly_report()` generates HTML with 4-week table | unit | `pytest tests/test_quality_report.py -x` | Wave 0 |
| QC-06 | Degrading and improving scrapers correctly identified by > 10% delta | unit | `pytest tests/test_quality_report.py::test_anomaly_detection -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_quality_aggregator.py tests/test_quality_dashboard.py tests/test_quality_report.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_quality_aggregator.py` — covers QC-02, QC-03 (compute + persist logic with mocked Session)
- [ ] `tests/test_quality_dashboard.py` — covers QC-04 (endpoint shape, cache behavior, status classification)
- [ ] `tests/test_quality_report.py` — covers QC-05, QC-06 (HTML generation, anomaly detection, week-over-week delta)

Existing `tests/conftest.py` provides shared fixtures — no new conftest needed.

---

## Open Questions

1. **List of 11 active scraper names**
   - What we know: CONTEXT.md refers to "all 11 active scrapers"; `audit_data_quality.py` queries `PaddleMaster`+`MarketOffer` tables but does not enumerate scraper names explicitly
   - What's unclear: The canonical list of scraper names as strings (needed for matrix `strategy.matrix.scraper` and for `quality_aggregator.py`'s `ACTIVE_SCRAPERS` constant)
   - Recommendation: Planner should add a task to read `scripts/` directory for scraper filenames OR query `SELECT DISTINCT store_name FROM market_offers` to derive the list. The `slo_validator.py` `--all` flag iterates over `store_name` values from the DB — same approach should work.

2. **coverage_pct field list (Claude's discretion)**
   - What we know: `audit_data_quality.py` defines `REQUIRED_FIELDS` (9 fields) for `specs_confidence`; those are PaddleMaster fields, not MarketOffer fields
   - What's unclear: For `quality_aggregator.py`, `coverage_pct` should measure per-scraper data completeness — likely `price_brl`, `url`, `store_name`, `is_active`, `last_updated` on `MarketOffer`
   - Recommendation: Define `OFFER_REQUIRED_FIELDS = ['price_brl', 'url', 'store_name', 'last_updated']` for coverage_pct; document rationale in the aggregator module.

---

## Sources

### Primary (HIGH confidence)

- `app/models/slo.py` — QualityMetric model pattern (SQLModel + JSONB)
- `app/services/slo_alerts.py` — email transport reuse for weekly report
- `app/api/routes.py` — FastAPI router registration + `cachetools.TTLCache` pattern
- `.github/workflows/slo-check.yml` — matrix strategy, cron, workflow_dispatch skeleton
- `scripts/audit_data_quality.py` — existing metric calculation logic (freshness, field coverage)
- `app/db/database.py` — sync_engine + import registration pattern for Alembic

### Secondary (MEDIUM confidence)

- PostgreSQL `DISTINCT ON` for latest-row-per-group — standard PostgreSQL docs pattern, consistent with project's raw `text()` SQL usage in `deploy_validator.py`
- `pandas.DataFrame.groupby + isocalendar().week` for ISO week aggregation — pandas 2.2 docs

### Tertiary (LOW confidence)

- None — all findings verified against in-repo source code

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries confirmed present in requirements.txt and imported in codebase
- Architecture: HIGH — all patterns copied from prior phases with direct file references
- Pitfalls: HIGH — derived from actual code paths and established project decisions (Alembic imports, Actions secret scoping)
- Validation architecture: HIGH — test framework and pattern confirmed from 14 existing test files

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable stack; no external services introduced)
