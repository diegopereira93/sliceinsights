# Failure Mode Analysis

**Phase:** 3 — Automation & Reliability Mapping
**Requirements:** AUTO-03 (missing error recovery), LOG-02 (silent failures), LOG-05 (invisible failure modes)
**Date:** 2026-03-19

---

## Summary

The pipeline has three categories of failure modes: (1) hard failures that are immediately visible via non-zero exit codes, (2) soft failures that produce degraded output while exiting 0, and (3) invisible failures where the pipeline reports success but data quality has silently regressed. Categories 2 and 3 are the primary risk — they are the most common and have no current detection mechanism.

---

## Failure Mode Taxonomy

### Category A: Hard Failures (Visible)

These failures are detectable by `audit_runner.py` via non-zero exit codes or stderr output.

| Failure Mode | Trigger | Detection | Recovery |
|---|---|---|---|
| Python ImportError | Missing library | Immediate crash, exit 1 | Install dependency |
| PostgreSQL connection refused | DB not running | Immediate crash, exit 1 | Start DB |
| Playwright launch failure | Chromium not installed | Immediate crash, exit 1 | `playwright install chromium` |
| Unhandled exception at top level | Uncaught error in main | Immediate crash, exit 1 | Fix code |
| Script timeout (>N seconds) | Infinite loop / hung request | `audit_runner.py` SIGKILL | Add request timeout |

**Risk:** Low — these failures are loud and get fixed.

---

### Category B: Soft Failures (Partially Visible)

These failures produce reduced or degraded output but the scraper exits 0. The runner classifies these as SUCCESS.

| Failure Mode | Trigger | Symptom | Detection | Recovery |
|---|---|---|---|---|
| Pagination break on error | Exception on page N | Only pages 1..(N-1) scraped | None (exit 0) | None |
| Per-item parse skip (`continue`) | DOM change / bad data | N items skipped silently | None (exit 0) | None |
| Price coercion to 0.0 | Currency format change | Items saved with price=0 | None currently | Query `WHERE price = 0` |
| Partial DB write | Connection drop mid-batch | Some records written, rest lost | None (exit 0) | None |

**Risk:** High — data exists but is incomplete. Recommendations engine may act on stale/partial data.

---

### Category C: Invisible Failures (Silent)

These failures produce no error output and no observable degradation at the script level. The system has no way to distinguish them from a healthy run.

| Failure Mode | Trigger | Symptom | Current Detection | Impact |
|---|---|---|---|---|
| **CSS selector returns empty list** | Store theme update changes DOM structure | `soup.select(".product-card")` returns `[]`; loop body never executes; 0 products scraped | **None** — exits 0 with "Scraped 0 products" | Critical — entire store's catalog vanishes from DB on next write/upsert |
| **Pagination silently stops at page 1** | Store changes pagination URL structure | Only first page scraped; subsequent pages 404 or return empty | **None** — exits 0 | High — catalog appears complete but is truncated |
| **Count drop below baseline** | Any of the above, or store inventory decreases legitimately | Scraped 12 products vs historical 200 | **None** — no anomaly detection | High — impossible to distinguish bug from legitimate store change |
| **JS timeout (Playwright)** | Slow network, selector not present | `TimeoutError` caught, item skipped; run continues | Print statement only | High — unpredictable coverage on JS scrapers |
| **API rate limit (HTTP 429) silently handled** | Too many requests | Response body contains error JSON, not product data; parser produces 0 or garbage | **None** — status code not checked before parsing | Medium — rare but possible |
| **DB constraint violation suppressed** | Duplicate key or null constraint | Record not written; exception caught and continued | None | Medium — data loss without notification |

**Risk: Critical** — these are the dominant failure mode. A scraper can "succeed" while delivering zero value.

---

## Silent Failure Deep Dive

### Vector 1: Empty CSS Selector

```python
# Scraper code (simplified)
cards = soup.select(".product-card")  # returns [] after theme update
for card in cards:                    # loop never executes
    products.append(parse(card))

print(f"Scraped {len(products)} products")  # prints "Scraped 0 products"
# Script exits 0 — classified as SUCCESS
```

**Why it's invisible:** The script "completed successfully" from the OS perspective. Without a minimum product count assertion, this is indistinguishable from a store with no products.

### Vector 2: Partial Extraction with Price Default

```python
try:
    price_text = card.select_one(".price").get_text()
    price = float(price_text.replace("R$", "").replace(".", "").replace(",", "."))
except (AttributeError, ValueError):
    price = 0.0  # silent default
    continue     # item skipped or saved with price=0
```

**Why it's invisible:** Items are either skipped (reducing count with no alert) or saved with `price=0.0` (polluting the DB with invalid prices that look like valid records).

### Vector 3: Count Regression

A scraper that historically returns 180-220 products returns 14 after a CSS change. Without a baseline comparison, this looks identical to a successful run with a small product catalog.

---

## Current Alerting Coverage

| Alert Type | Implemented | Notes |
|---|---|---|
| Script crash / non-zero exit | Yes (audit only) | `audit_runner.py` captures exit codes |
| Product count anomaly detection | **No** | Planned for Phase 2 (QUAL-06) |
| Price = 0 anomaly | **No** | Could be queried post-run |
| Scraper duration anomaly | **No** | No baseline timing established |
| DB write failure notification | **No** | Exceptions caught and suppressed |
| Pipeline-level alerting (PagerDuty, Slack, etc.) | **No** | No alerting integration exists |

---

## Failure Recovery Gaps

| Gap | Affected Scrapers | Effort to Fix |
|---|---|---|
| No retry on transient HTTP errors | All (~24) | Medium — add `tenacity` to `scraper_utils.py` |
| No minimum product count assertion | All (~24) | Low — add post-scrape validation function |
| No pagination health check | Paginated scrapers (~16) | Medium — validate page N response before processing |
| No DB write error surfacing | All (~24) | Low — remove broad exception swallowing around DB calls |
| No anomaly detection for count regression | All (~24) | High — requires baseline tracking (Phase 2 QUAL-06) |

---

## Recommendations (for Phase 4 planning)

1. Add a `validate_scrape_result(products, scraper_name, min_expected)` function called before any DB write — raise if count is below threshold.
2. Replace `except Exception` around DB writes with specific exception types; let DB errors propagate to exit code.
3. Log a structured summary event at the end of every scraper run: `{scraper, count, skipped, duration, status}` — enables post-hoc anomaly detection even before full alerting is built.
4. Implement Phase 2 QUAL-06 (anomaly detection) to establish product count baselines and trigger alerts on regression.
