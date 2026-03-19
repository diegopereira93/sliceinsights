# Logging Coverage Report

**Phase:** 3 — Automation & Reliability Mapping
**Requirements:** LOG-01 (audit logging coverage), LOG-03 (where logs are stored), LOG-04 (structured vs unstructured)
**Date:** 2026-03-19

---

## Summary

Logging coverage is 100% unstructured `print()` statements. Python's `logging` module is not used in production scraper code. Logs exist only as ephemeral stdout/stderr during execution — no persistent centralized log store exists for production runs. During audits, `audit_runner.py` captures logs to per-scraper files in `test-results/`, but this is an audit-only mechanism not active in production.

---

## Coverage Inventory

| Component | Logging Method | Coverage Level | Structured? | Persistent? |
|---|---|---|---|---|
| Shopify scrapers | `print()` | Partial (start/end + errors) | No | No |
| HTML scrapers (Nuvemshop, WooCommerce) | `print()` | Partial (errors only) | No | No |
| Custom/Playwright scrapers | `print()` | Minimal (ad-hoc) | No | No |
| `audit_runner.py` | `print()` + stdout capture | Full (per-run) | No | Audit only |
| `measure_freshness.py` | `print()` + `logging` (SQLAlchemy suppression) | Partial | No | No |
| `measure_coverage.py` | `print()` | Partial | No | No |
| Pipeline orchestration | `print()` | Minimal | No | No |

**Overall structured logging coverage: 0%**
**Overall persistent logging coverage (production): 0%**

---

## Storage Location

### Audit Runs (non-production)

During `audit_runner.py` execution, logs are captured to:

```
test-results/
  scraper_audit_<timestamp>.log   # combined log per audit run
  <scraper_name>_stdout.log       # per-scraper stdout
  <scraper_name>_stderr.log       # per-scraper stderr
```

These files are created only when the audit harness runs. They are not produced during production pipeline execution.

### Production Runs

| Trigger | Log destination | Retention |
|---|---|---|
| GitHub Actions `production-pipeline.yml` | GitHub Actions run log (ephemeral) | 90 days (GitHub default) |
| GitHub Actions `price-monitoring.yml` | GitHub Actions run log (ephemeral) | 90 days (GitHub default) |
| Manual execution | Terminal stdout only | None (lost on session close) |
| Docker container exec | Container stdout | Until container restart |

**No centralized log aggregation system exists (no ELK, CloudWatch, Datadog, etc.).**

---

## Log Format Analysis

### Current Format (Representative Samples)

```
# Typical scraper startup
Fetching products from store: https://example.myshopify.com/products.json
Page 1: 250 products
Page 2: 187 products
Total: 437 products scraped

# Typical error log
Error parsing product: 'NoneType' object has no attribute 'get_text'
Error on page 3: HTTPSConnectionPool(...): Read timed out.

# Emoji-decorated format (used in some scrapers)
✅ Scraped 200 products from store X
⚠️ Skipped 3 products due to parse errors
📦 Saving to database...
```

### Format Problems

| Issue | Impact |
|---|---|
| Free-text strings — no key=value pairs | Cannot parse log fields programmatically |
| No timestamp per log line | Cannot correlate events or measure duration |
| No log level (INFO/WARN/ERROR) | Cannot filter by severity |
| No scraper identifier in each line | In aggregated logs, source is ambiguous |
| No run ID / correlation ID | Cannot trace a single pipeline execution end-to-end |
| Emoji characters | Breaks log parsers that expect ASCII |
| Inconsistent: some errors printed, some silent | Cannot distinguish "ran cleanly" from "ran with suppressed errors" |

---

## Python `logging` Module Usage

The standard `logging` module is used in **one place only**:

```python
# In measure_coverage.py — suppressing SQLAlchemy noise
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

This is a suppression call, not an actual logging implementation. No scraper uses `logging.info()`, `logging.error()`, `logging.warning()`, or any handler configuration.

---

## Gap Analysis

| LOG Requirement | Current State | Gap |
|---|---|---|
| LOG-01: Audit logging coverage | 100% `print()`, 0% structured | All scrapers need structured logging |
| LOG-03: Log storage location | stdout + ephemeral CI logs only | No persistent log store for production |
| LOG-04: Structured vs unstructured | 100% unstructured | Full migration to structured logging needed |

---

## Recommendations (for Phase 4 planning)

1. Replace all `print()` calls with `structlog` or `logging` + JSON formatter to produce machine-parsable log lines.
2. Add mandatory fields to every log event: `timestamp`, `scraper_name`, `run_id`, `level`, `event`.
3. Configure a log handler that writes to a persistent store (file, cloud logging, or database `pipeline_runs` table).
4. Remove emoji characters from log messages; use log level fields instead.
5. Standardize a post-run summary log event with: `scraper`, `products_scraped`, `products_skipped`, `duration_seconds`, `status`.
