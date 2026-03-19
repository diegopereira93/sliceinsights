# SLO Enforcement & Validation Guide

**Phase:** 6 — SLO Enforcement & Validation
**Last Updated:** 2026-03-19
**Owner:** Data Engineering

---

## Overview

This guide documents the SliceInsights SLO (Service Level Objective) enforcement system. It covers:

- What SLOs are defined and why
- How the system validates them (real-time and scheduled)
- The database schema that stores all results
- How to configure thresholds
- Operational procedures for debugging and responding to breaches

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   SLO Enforcement System                      │
│                                                              │
│  ┌─────────────────┐         ┌──────────────────────────┐   │
│  │  Scraper (any)  │         │  GitHub Actions Cron     │   │
│  │                 │         │  .github/workflows/      │   │
│  │  main()         │         │  slo-check.yml           │   │
│  │     ↓           │         │  Runs every 6 hours      │   │
│  │  finish_run()   │         │  (00:00, 06:00, 12:00,   │   │
│  │  [scraper_utils]│         │   18:00 UTC)             │   │
│  └────────┬────────┘         └──────────┬───────────────┘   │
│           │                             │                    │
│           │  validate_job_slo()         │  --all             │
│           └──────────┬──────────────────┘                   │
│                      ↓                                       │
│          ┌───────────────────────┐                          │
│          │  scripts/             │                          │
│          │  slo_validator.py     │                          │
│          │                       │                          │
│          │  check_freshness()    │  → market_offers table   │
│          │  check_completeness() │  → paddle_master table   │
│          └──────────┬────────────┘                          │
│                     ↓                                       │
│          ┌──────────────────────┐                           │
│          │  PostgreSQL          │                           │
│          │  slo_logs table      │                           │
│          │  (queryable by       │                           │
│          │   Phase 7 Alerts)    │                           │
│          └──────────────────────┘                           │
└──────────────────────────────────────────────────────────────┘
```

**Design principle:** A single validation module (`slo_validator.py`) is consumed two ways — real-time after each scraper run, and scheduled via cron. Both paths write identical rows to `slo_logs`, so all results are queryable regardless of how the check was triggered.

---

## SLO Thresholds

| SLO | Metric | Table | Threshold | Requirement |
|-----|--------|-------|-----------|-------------|
| Freshness | Age of newest `market_offers` record per store | `market_offers` | 24 hours | SLO-03 |
| Completeness | Age of newest `paddle_master` record | `paddle_master` | 7 days (168 hours) | SLO-04 |

### Configuration

Thresholds are centralized in `scripts/slo_config.py`:

```python
# SLO-03: Market Offers (prices) must be refreshed within 24 hours
FRESHNESS_SLO_HOURS = 24

# SLO-04: Product Master Data (specs) must be refreshed within 7 days
COMPLETENESS_SLO_DAYS = 7
COMPLETENESS_SLO_HOURS = COMPLETENESS_SLO_DAYS * 24  # 168
```

To change a threshold, edit this file only. Both the real-time hook and the scheduled job import from here.

---

## Database Schema

### `slo_logs` table

Created via Alembic migration `d081a2cccc0e_add_slo_logs_table.py`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial PK | Auto-increment primary key |
| `scraper_name` | varchar (indexed) | Store name (e.g. `mercado_livre`) or `__all__` for batch runs |
| `metric_type` | varchar | `freshness` or `completeness` |
| `value_hours` | float | Measured age in hours. `99999.0` means no data found |
| `threshold_hours` | float | Configured threshold at the time of the check |
| `status` | varchar | `pass` or `fail` |
| `checked_at` | timestamptz | UTC timestamp when the check ran |
| `details` | jsonb | Extra context — see below |

### `details` JSONB examples

**Freshness pass:**
```json
{
  "newest_record": "2026-03-19 18:45:00+00:00",
  "age_hours": 2.3
}
```

**Freshness fail (stale data):**
```json
{
  "newest_record": "2026-03-18 10:00:00+00:00",
  "age_hours": 32.75
}
```

**No data (scraper never ran or table empty):**
```json
{
  "reason": "no_data"
}
```

**Completeness fail:**
```json
{
  "newest_updated_at": "2026-03-11 12:00:00+00:00",
  "age_hours": 194.5
}
```

---

## Validation Engine

### `scripts/slo_validator.py`

#### `check_freshness(session, scraper_name=None)`

Groups `market_offers` by `store_name` and compares `MAX(last_updated)` age to `FRESHNESS_SLO_HOURS`. Writes one `SLOLog` row per store.

- `scraper_name=None` checks all active stores
- `scraper_name="mercado_livre"` checks only that store
- Records with `is_active=False` are excluded

**Key behavior:** If no rows exist (empty table or no active offers), writes a single `fail` row with `value_hours=99999.0` and `details={"reason": "no_data"}`.

#### `check_completeness(session, scraper_name=None)`

Queries `MAX(paddle_master.updated_at)` across the entire catalog and compares to `COMPLETENESS_SLO_HOURS`. Writes one `SLOLog` row.

- The `scraper_name` parameter is accepted for API symmetry but `paddle_master` is a global catalog — the check always covers all rows
- When called with `--all`, uses `scraper_name="__all__"` in the log

#### `validate_job_slo(scraper_name)`

Non-blocking real-time hook for scrapers:

```python
def validate_job_slo(scraper_name: str) -> None:
    try:
        init_db_sync()
        with Session(sync_engine) as session:
            check_freshness(session, scraper_name=scraper_name)
    except Exception as exc:
        print(f"[WARN] SLO validation failed (non-blocking): {exc}")
```

This function **never raises**. If the DB is unreachable or the check fails, it prints a warning and returns. Scraper exit code is always 0.

---

## Scheduled Workflow

**File:** `.github/workflows/slo-check.yml`

**Schedule:** `cron: '0 */6 * * *'` — runs at 00:00, 06:00, 12:00, 18:00 UTC daily (4 runs per day).

**Manual trigger:** Go to GitHub Actions tab → "SLO Validation" workflow → "Run workflow".

**Secret required:** `DATABASE_URL_SYNC` must be set in GitHub Repository Secrets with the production PostgreSQL connection string.

```
postgresql://user:password@host:5432/picklematch
```

**Failure behavior:** `continue-on-error: true` at the job level. SLO validation failures surface as a yellow warning in the Actions UI but never block other workflows or fail the run.

---

## Real-time Integration

Scrapers trigger SLO validation automatically via `finish_run()` in `scripts/scraper_utils.py`:

```python
def finish_run(scraper_name: str) -> None:
    print(f"[SLO] SLO validation triggered for {scraper_name}")
    try:
        from scripts.slo_validator import validate_job_slo
        validate_job_slo(scraper_name)
    except Exception as exc:
        print(f"[SLO] WARNING: SLO validation failed (non-blocking): {exc}")
```

The unified scraper dispatcher (`scripts/run_scraper.py`) calls `finish_run()` after each scraper's `main()` returns. This guarantees the freshness check sees the data just committed.

**Invocation path:**
```
run_scraper.py --scraper mercado_livre
  → module.main()       (data committed to DB)
  → finish_run("mercado_livre")
      → validate_job_slo("mercado_livre")
          → check_freshness(session, "mercado_livre")
              → SLOLog written to slo_logs
```

---

## CLI Usage

Run the validator manually from the project root:

```bash
# Set connection string (use localhost:5434 when running from host machine)
export DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5434/picklematch

# Check all stores and global catalog
python scripts/slo_validator.py --all

# Check a single store
python scripts/slo_validator.py --scraper mercado_livre
```

**Example output:**
```
[freshness] mercado_livre: PASS (age=3.2h, threshold=24h)
[freshness] paddle_palace: FAIL (age=26.1h, threshold=24h)
[completeness] __all__: PASS (age=48.3h, threshold=168h)
[slo_validator] Done.
```

---

## SQL Queries for Debugging

### View recent checks

```sql
SELECT scraper_name, metric_type, status, value_hours, threshold_hours, checked_at
FROM slo_logs
ORDER BY checked_at DESC
LIMIT 20;
```

### All active breaches (latest check per store)

```sql
SELECT DISTINCT ON (scraper_name, metric_type)
    scraper_name,
    metric_type,
    status,
    value_hours,
    threshold_hours,
    checked_at,
    details
FROM slo_logs
WHERE status = 'fail'
ORDER BY scraper_name, metric_type, checked_at DESC;
```

### Freshness breach summary

```sql
SELECT status FROM slo_logs
WHERE metric_type = 'freshness' AND status = 'fail'
LIMIT 1;
```

### Completeness breach summary

```sql
SELECT status FROM slo_logs
WHERE metric_type = 'completeness' AND status = 'fail'
LIMIT 1;
```

### Check JSONB details for a breach

```sql
SELECT scraper_name, details, checked_at
FROM slo_logs
WHERE status = 'fail'
ORDER BY checked_at DESC
LIMIT 5;
```

### Count breaches in last 24 hours

```sql
SELECT metric_type, COUNT(*) as breach_count
FROM slo_logs
WHERE status = 'fail'
  AND checked_at > NOW() - INTERVAL '24 hours'
GROUP BY metric_type;
```

### History for a specific store

```sql
SELECT metric_type, status, value_hours, checked_at
FROM slo_logs
WHERE scraper_name = 'mercado_livre'
ORDER BY checked_at DESC
LIMIT 20;
```

---

## Breach Simulation (Testing)

Use these commands to verify the system detects breaches correctly.

### Freshness breach simulation

```bash
export DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5434/picklematch

# Age one store's offers to 25 hours ago
psql $DATABASE_URL_SYNC -c "
  UPDATE market_offers
  SET last_updated = NOW() - INTERVAL '25 hours'
  WHERE store_name = (SELECT DISTINCT store_name FROM market_offers LIMIT 1)
    AND is_active = true;
"

# Run validator
python scripts/slo_validator.py --all

# Verify breach logged
psql $DATABASE_URL_SYNC -c "
  SELECT scraper_name, status, value_hours, checked_at
  FROM slo_logs
  WHERE metric_type = 'freshness' AND status = 'fail'
  ORDER BY checked_at DESC LIMIT 1;
"
```

**Expected result:** One row with `status='fail'` and `value_hours > 24`.

### Completeness breach simulation

```bash
# Age paddle_master to 8 days ago
psql $DATABASE_URL_SYNC -c "
  UPDATE paddle_master
  SET updated_at = NOW() - INTERVAL '8 days'
  WHERE id = (SELECT id FROM paddle_master LIMIT 1);
"

# Run validator
python scripts/slo_validator.py --all

# Verify breach logged
psql $DATABASE_URL_SYNC -c "
  SELECT scraper_name, status, value_hours, checked_at
  FROM slo_logs
  WHERE metric_type = 'completeness' AND status = 'fail'
  ORDER BY checked_at DESC LIMIT 1;
"
```

**Expected result:** One row with `status='fail'` and `value_hours > 168`.

---

## Runbook: Common Failures

### Freshness SLO breach — stale market offers

**Symptom:** `slo_logs` row with `metric_type='freshness'`, `status='fail'`, `value_hours > 24` for a specific `scraper_name`.

**Diagnosis:**
```sql
-- Find oldest records for the failing store
SELECT store_name, MAX(last_updated) as newest, COUNT(*) as row_count
FROM market_offers
WHERE store_name = '<scraper_name>' AND is_active = true
GROUP BY store_name;
```

**Possible causes:**
1. Scraper has not run recently — check GitHub Actions run history for the scraper's workflow
2. Scraper ran but failed silently — check for error rows or empty results in `market_offers`
3. Scraper ran but data was written with wrong `store_name` — query without the store filter

**Resolution:**
1. Trigger the scraper manually: `python scripts/run_scraper.py --scraper <name>`
2. Verify new data appears: `SELECT MAX(last_updated) FROM market_offers WHERE store_name = '<name>';`
3. Re-run validator to confirm `pass`: `python scripts/slo_validator.py --scraper <name>`

---

### Freshness SLO breach — no data (`reason: no_data`)

**Symptom:** `slo_logs` row with `value_hours=99999.0` and `details={"reason": "no_data"}`.

**Diagnosis:** The `market_offers` table has no active rows for this store at all.

```sql
SELECT COUNT(*) FROM market_offers WHERE store_name = '<name>' AND is_active = true;
-- Returns 0
```

**Resolution:**
1. Run the scraper: `python scripts/run_scraper.py --scraper <name>`
2. If the scraper fails, check network connectivity to the store's website
3. If the store is discontinued, deactivate it from the scraper config

---

### Completeness SLO breach — stale paddle catalog

**Symptom:** `slo_logs` row with `metric_type='completeness'`, `status='fail'`, `value_hours > 168`.

**Diagnosis:**
```sql
SELECT MAX(updated_at) as newest, COUNT(*) as total_paddles FROM paddle_master;
```

**Possible causes:**
1. Paddle catalog ingestion has not run in over 7 days
2. `updated_at` field not being set during upserts

**Resolution:**
1. Run the catalog update job manually
2. Verify `MAX(updated_at)` advances
3. Re-run validator: `python scripts/slo_validator.py --all`

---

### Scheduled workflow not running

**Symptom:** No `slo_logs` rows with `checked_at` in the last 6+ hours.

**Diagnosis:**
1. Check `.github/workflows/slo-check.yml` is present on the default branch
2. Go to GitHub Actions tab → verify the "SLO Validation" workflow appears
3. Check `DATABASE_URL_SYNC` secret is set in Repository Settings → Secrets

**Common fix:** GitHub Actions cron schedules are delayed during periods of high load. Trigger manually via "Run workflow" to confirm the workflow itself is functional.

---

### `DATABASE_URL_SYNC` not set (local development)

**Symptom:** `slo_validator.py` fails immediately with a connection error.

**Fix:**
```bash
# From host machine (postgres runs on port 5434 externally)
export DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5434/picklematch

# Or inside Docker network
export DATABASE_URL_SYNC=postgresql://postgres:postgres@postgres_v3:5432/picklematch
```

---

## Integration with Phase 7 Alerts

The `slo_logs` table is the data source for Phase 7 alerting. The alert system queries for recent `fail` rows and fires notifications via Telegram, GitHub Issues, and email.

The recommended query for Phase 7 to detect active breaches:

```sql
SELECT scraper_name, metric_type, value_hours, threshold_hours, checked_at, details
FROM slo_logs
WHERE status = 'fail'
  AND checked_at > NOW() - INTERVAL '7 hours'
ORDER BY checked_at DESC;
```

A 7-hour window is used (slightly wider than the 6-hour cron interval) to account for scheduling jitter.

---

## Requirements Traceability

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| SLO-01 | Real-time SLO validation after each scraper completes | `finish_run()` in `scraper_utils.py` + `validate_job_slo()` |
| SLO-02 | Scheduled SLO validation 4x daily | `.github/workflows/slo-check.yml` cron `0 */6 * * *` |
| SLO-03 | Freshness SLO: 24h for Market Offers | `check_freshness()` + `FRESHNESS_SLO_HOURS=24` |
| SLO-04 | Completeness SLO: 7d for Product Master Data | `check_completeness()` + `COMPLETENESS_SLO_HOURS=168` |
| SLO-05 | SLO results logged and queryable | `slo_logs` table with JSONB details column |

---

*Guide created as part of Phase 6 (SLO Enforcement & Validation) — 2026-03-19*
