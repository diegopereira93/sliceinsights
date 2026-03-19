# Automation & Error Handling Audit

**Phase:** 3 — Automation & Reliability Mapping
**Requirements:** AUTO-01 (retry logic), AUTO-02 (error handling patterns)
**Date:** 2026-03-19

---

## Summary

None of the 24 scrapers implement retry logic. All use a single `requests.get` or Playwright call per page with no recovery mechanism for transient failures. Error handling follows a uniform broad `except Exception` pattern that silently drops failed items.

---

## Error Handling Pattern Comparison

| Scraper Category | try/except Present | Scope | On Exception | Retry Logic | Notes |
|---|---|---|---|---|---|
| Shopify JSON (API) | Yes | Per product card | `continue` (item skipped) | None | Most consistent pattern; structured JSON reduces parse errors |
| Nuvemshop / TiendaNube (HTML) | Yes | Per product card | `continue` (item skipped) | None | DOM-dependent; CSS selector changes cause silent drops |
| WooCommerce (HTML) | Yes | Per product card | `continue` (item skipped) | None | Similar to Nuvemshop pattern |
| Custom storefronts (JS) | Yes | Per page / selector | `break` or `continue` | None | Playwright auto-waiting masks some failures; no script-level retry |
| `scrape_justpaddles.py` | Yes | Per product | `continue` | None | Uses Playwright; single timeout = entire run fails |
| `audit_runner.py` | Yes | Per script execution | Log + categorize | None | Categorizes as: timeout / code error / parser error |

### Retry Logic Coverage

| Requirement | Status | Detail |
|---|---|---|
| Network-level retries (502/503/504) | **MISSING** | No `tenacity`, `backoff`, or manual retry loops found anywhere |
| Pagination recovery | **MISSING** | Failure on page N drops all pages N+1..end |
| Playwright timeout recovery | **MISSING** | A single selector timeout aborts the entire session |
| Partial scrape recovery | **MISSING** | No checkpointing; failed mid-run means data loss from that point |

---

## Standard Error Handling Pattern (Representative)

```python
# Pattern found across ~20 of 24 scrapers
for card in soup.select(".product-card"):
    try:
        name = card.select_one(".product-name").get_text(strip=True)
        price = float(card.select_one(".price").get_text().replace("R$", "").strip())
        products.append({"name": name, "price": price})
    except Exception as e:
        print(f"Error parsing product: {e}")  # or sometimes silent
        continue
```

**Problems with this pattern:**
1. Broad `except Exception` catches everything — parse errors, attribute errors, network errors all treated identically.
2. `continue` means item is silently dropped with no count of how many were lost.
3. `print()` output is unstructured — not machine-parsable, not aggregatable.
4. No distinction between recoverable (transient network) and unrecoverable (DOM changed) errors.

---

## Pagination Error Pattern

```python
# Pattern found in paginated scrapers
for page in range(1, 100):
    try:
        response = requests.get(url, timeout=30)
        ...
    except Exception as e:
        print(f"Error on page {page}: {e}")
        break  # or continue — inconsistent across scrapers
```

**Problems:**
- `break` on page 5 of 10 = 5 pages of products lost silently.
- `continue` skips that page but continues — may produce duplicate-free but sparse data.
- No HTTP status code inspection before parsing (200 OK assumed).

---

## `audit_runner.py` — External Retry Context

`audit_runner.py` wraps scraper execution and captures exit codes, but:
- It does NOT retry failed scrapers automatically.
- It categorizes failures post-hoc (timeout/code/parser) for reporting.
- Individual scraper partial failures are invisible to the runner — a scraper that exits 0 with 12 products instead of 200 is classified as SUCCESS.

---

## Risk Assessment

| Risk | Severity | Likelihood | Notes |
|---|---|---|---|
| Transient HTTP 503 → permanent data loss for run | High | Medium | Happens during store maintenance windows |
| CSS selector change → 0 products scraped, logged as success | Critical | High | No DOM version pinning or count validation |
| Playwright timeout → entire JS scraper run lost | High | Medium | justpaddles, PB Studio most at risk |
| Page 5+ drop on pagination failure | High | Medium | All paginated scrapers affected |

---

## Recommendations (for Phase 4 planning)

1. Integrate `tenacity` into `scraper_utils.py` for all `requests.get` calls with exponential backoff on 429/502/503/504.
2. Replace broad `except Exception` with typed exception handlers — separate `requests.exceptions.Timeout`, `AttributeError` (parse), `ValueError` (data coercion).
3. Add post-run product count assertions: if `len(products) < expected_minimum`, raise alert rather than exiting 0.
4. Add Playwright retry wrapper in `fetch_dynamic_products` for selector timeouts.
