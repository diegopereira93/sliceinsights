# Phase 3 Research: Automation & Reliability Mapping

## Objective
Document error handling, retry logic, logging, dependencies, and identify automation gaps across the 24 scrapers and pipeline scripts.

## Findings Summary

### 1. Retry Logic (AUTO-01, AUTO-03)
*   **Current State:** There is **no systematic retry logic** across the scrapers. Packages like `tenacity` or `backoff` are not used. 
*   **Pattern:** Scrapers typically use a single `requests.get` call per page. If a timeout or HTTP error occurs, the loop either `break`s (losing all subsequent pages) or `continue`s (losing that specific page).
*   **Playwright Scripts:** Scripts using Playwright (e.g., `fetch_dynamic_products` in `scraper_utils.py` and `scrape_justpaddles.py`) rely on Playwright's built-in auto-waiting for selectors, but lack explicit script-level retries for catastrophic network failures or timeouts.
*   **Missing Error Recovery:** 
    *   No network-level retries for transient HTTP errors (502, 503, 504).
    *   No recovery for partial scrapes; a failure on page 5 of 10 drops all subsequent data.

### 2. Error Handling Patterns (AUTO-02)
*   **Broad Excepts:** The standard pattern is a broad `try...except Exception as e:` block inside the parsing loop. 
*   **Silent Drops:** When an exception occurs parsing a specific product card, it is caught, occasionally printed, and skipped via `continue`. This makes parser failures (e.g., due to DOM changes) fail silently on a per-item basis.
*   **Exit Codes:** `audit_runner.py` wraps executions and detects failures via standard error and non-zero exit codes, categorizing them as timeouts, code errors, or parser errors. However, the individual scrapers themselves do not bubble up partial failures effectively.

### 3. Dependencies (AUTO-05)
*   **Python Libraries:** `requests`, `beautifulsoup4`, `playwright`, `sqlmodel`, `dlt`, `openai`.
*   **External APIs & Platforms:**
    *   Shopify JSON APIs (e.g., `/products.json`)
    *   Nuvemshop / TiendaNube HTML storefronts
    *   WooCommerce HTML storefronts
    *   Custom storefronts (JustPaddles, PB Studio, etc.)
*   **Infrastructure:** PostgreSQL database, Docker (for Playwright environments).

### 4. Logging Coverage (LOG-01, LOG-03, LOG-04)
*   **Coverage:** 100% unstructured `print()` statements. Python's standard `logging` module is NOT used (except to suppress SQLAlchemy warnings in `measure_coverage.py`).
*   **Storage:** Logs are only available via stdout/stderr. During an audit, `audit_runner.py` captures these to `test-results/scraper_audit_*.log`, but there is no centralized logging mechanism for production runs.
*   **Format:** Unstructured text, occasionally using emojis (e.g., `✅`, `⚠️`, `📦`) for visual grepping. Not machine-parsable.

### 5. Invisible Failure Modes & Silent Failures (LOG-02, LOG-05)
*   **Empty Result Sets:** If a CSS selector changes, `soup.select()` returns an empty list. The loop silently breaks, and the script exits successfully with 0 products scraped. The system has no way to distinguish between "store is empty" and "CSS selector broke".
*   **Partial Extraction:** If the price extraction regex fails (e.g., store changes currency format), the item's price defaults to 0.0 or throws an error. If caught, the item is skipped. The run succeeds but with reduced coverage.
*   **Silent Failures:** The current architecture hides partial failures. A script that typically scrapes 200 items might drop to 50 due to a pagination bug, but without anomaly detection (Phase 2 QUAL-06), this failure mode is entirely invisible.

### 6. Data Freshness SLOs (AUTO-04)
*   **Current State:** Tracking exists via `measure_freshness.py` (which calculates the age of `MarketOffer` records).
*   **Proposed SLO:** 
    *   **Prices & Availability (Market Offers):** Refreshed every 24 hours (Daily).
    *   **Product Master Data (Specs):** Refreshed weekly or on-demand (changes infrequently).

## Next Steps for Planning
1.  **Standardize Retry Logic:** Plan the integration of a retry library (e.g., `tenacity`) into `scraper_utils.py` for network and HTTP operations.
2.  **Upgrade Logging:** Plan migration from `print()` to structured logging (e.g., `structlog` or `logging` with JSON format) to enable automated alerting and log aggregation.
3.  **Implement Anomaly Detection (Coverage Gates):** Plan a mechanism to detect and alert on sudden drops in scraped product counts (e.g., "Expected ~150 products, got 12 -> TRIGGER ALERT").
4.  **Define Phase 3 Deliverables:** The deliverables are documents (Dependency Matrix, Error Comparison, Logging Report, SLO Spec, Failure Analysis). These can be generated based on this research and the Phase 1/2 outputs.
