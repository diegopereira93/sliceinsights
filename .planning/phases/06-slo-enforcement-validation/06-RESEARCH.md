# Phase 6: SLO Enforcement & Validation — Research

**Researched:** 2026-03-19
**Phase Req IDs:** SLO-01, SLO-02, SLO-03, SLO-04, SLO-05

## Executive Summary

The recommended approach uses a centralized SLO validation module (`scripts/slo_validator.py`) that handles both real-time post-scraper hooks and scheduled GitHub Actions runs. The module exposes `check_freshness()` and `check_completeness()` as standalone functions importable by scrapers. A new `slo_logs` table with JSONB breach details column is added via Alembic. Configuration constants live in `scripts/slo_config.py`. Real-time hooks are non-blocking (try/except); scheduled checks run via cron on every 6 hours.

---

## 1. SLO Validation Architecture

**Pattern:** Centralized module with dual-entry points.

- All SLO logic lives in `scripts/slo_validator.py`
- **Real-time**: Scrapers call `validate_job_slo(scraper_name)` after committing data
- **Scheduled**: GitHub Actions runs `python scripts/slo_validator.py --all` via cron
- Separate functions: `check_freshness(session, scraper_name)` and `check_completeness(session, scraper_name)` for granular reporting
- Results are always written to `slo_logs` table regardless of invocation mode

**Key decision:** Single module consumed two ways — avoids duplication, ensures real-time and scheduled checks use identical logic.

---

## 2. GitHub Actions Scheduling

**Cron Configuration (SLO-02):**

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'   # every 6 hours: 00:00, 06:00, 12:00, 18:00 UTC
  workflow_dispatch: {}      # allows manual trigger from Actions tab
```

**Secrets Management:**
- Store production DB connection string as `DATABASE_URL_PROD` in GitHub Repository Secrets
- Inject in workflow env: `DATABASE_URL_SYNC: ${{ secrets.DATABASE_URL_PROD }}`
- No GHA service container needed — connects directly to existing production PostgreSQL

**Pattern from existing ci.yml:**
- Use `actions/checkout@v4` + `actions/setup-python@v5` with `python-version: '3.11'`
- Install `pip install -r requirements.txt`
- Run `python scripts/slo_validator.py --all`

---

## 3. Database Schema for SLO Logs

**SQLModel table definition:**

```python
class SLOLog(SQLModel, table=True):
    __tablename__ = "slo_logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    scraper_name: str                           # e.g. "mercado_livre", "__all__"
    metric_type: str                            # "freshness" | "completeness"
    value_hours: float                          # measured age in hours
    threshold_hours: float                      # configured threshold
    status: str                                 # "pass" | "fail"
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    details: Dict = Field(default={}, sa_column=Column(JSONB))
    # details: {"breach_count": 3, "oldest_record_id": 42, "scraper": "loja_x"}
```

**Migration approach:**
- Follow existing pattern in `alembic/versions/` (see `837c5f246923_add_validation_sources_to_paddle.py`)
- Run `alembic revision --autogenerate -m "add slo_logs table"` then `alembic upgrade head`
- Import `SLOLog` in `app/db/database.py` or wherever models are registered so SQLModel picks it up

---

## 4. SLO Thresholds & Configuration

**Config file: `scripts/slo_config.py`**

```python
# SLO threshold constants
FRESHNESS_SLO_HOURS = 24        # Market Offers (prices) — SLO-03
COMPLETENESS_SLO_DAYS = 7       # Product Master Data (specs) — SLO-04

# Derived
COMPLETENESS_SLO_HOURS = COMPLETENESS_SLO_DAYS * 24
```

**Freshness measurement (SLO-03):**
- Query: `SELECT MAX(EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600) FROM market_offers WHERE is_active = true GROUP BY scraper_name`
- Alert if any scraper's max age > 24 hours

**Completeness measurement (SLO-04):**
- Query: `SELECT MAX(EXTRACT(EPOCH FROM (NOW() - MAX(updated_at)))/3600) FROM paddles`
- Alert if max age > 168 hours (7 days)

**Note:** `Paddle.updated_at` and `MarketOffer.updated_at` fields need to exist. If not present, this phase must add them.

---

## 5. Real-time Integration Pattern

**Hook location:** Call at the very end of scraper `main()`, after session.commit() and session.close().

**Non-blocking implementation:**
```python
# In scraper main():
try:
    from scripts.slo_validator import validate_job_slo
    validate_job_slo(scraper_name="mercado_livre")
except Exception as e:
    print(f"[WARN] SLO validation failed (non-blocking): {e}")
    # Scraper exits 0 regardless — SLO check failure never halts ingestion
```

**Why non-blocking:** Reporting failure must never prevent data collection. The SLO check writes a `fail` row to `slo_logs` which Phase 7 (Alerts) will pick up. The scraper's job is data ingestion, not alerting.

---

## 6. Existing Codebase Patterns

**Key files to reuse/extend:**

| File | How to use |
|------|-----------|
| `scripts/scraper_utils.py` | Import `get_session()` or sync session pattern |
| `scripts/audit_data_quality.py` | Reference for DB query patterns (SQLModel `session.exec`, `select`) |
| `scripts/measure_freshness.py` | Core freshness logic — can be extracted/wrapped |
| `.github/workflows/ci.yml` | Template for new `slo-check.yml` structure |
| `alembic/versions/837c5f246923_*.py` | Migration template for `slo_logs` table |

**Session pattern:** Use synchronous session (`DATABASE_URL_SYNC` env var) for scripts; avoid async context complexity in standalone CLI scripts.

---

## Validation Architecture

### How to verify each SLO requirement post-implementation:

**SLO-01 (Real-time hook):**
```bash
# Run any scraper, then check slo_logs table
python scripts/slo_validator.py --scraper mercado_livre
psql $DATABASE_URL_SYNC -c "SELECT * FROM slo_logs ORDER BY checked_at DESC LIMIT 5;"
# Expected: at least 1 row with scraper_name = 'mercado_livre'
```

**SLO-02 (Scheduled workflow):**
```bash
# Manual trigger from GitHub Actions tab → "Run workflow" button
# Verify: job completes with exit 0; slo_logs shows checked_at within last 5 minutes
```

**SLO-03 (Freshness threshold):**
```bash
# Simulate breach: update a MarketOffer's updated_at to 25h ago
# Then run validator: python scripts/slo_validator.py --all
# Expect: slo_logs row with metric_type='freshness', status='fail', value_hours > 24
```

**SLO-04 (Completeness threshold):**
```bash
# Simulate breach: update a Paddle's updated_at to 8 days ago
# Then run validator: python scripts/slo_validator.py --all
# Expect: slo_logs row with metric_type='completeness', status='fail', value_hours > 168
```

**SLO-05 (Queryable logs):**
```bash
# Verify table exists and is queryable
psql $DATABASE_URL_SYNC -c "SELECT scraper_name, metric_type, status, checked_at FROM slo_logs WHERE status = 'fail' ORDER BY checked_at DESC;"
# Expected: returns rows (or empty set if no active breaches)
# Also verify JSONB: psql -c "SELECT details FROM slo_logs LIMIT 1;" — must return valid JSON
```

---

*Research completed: 2026-03-19*

---
*RESEARCH COMPLETE*
