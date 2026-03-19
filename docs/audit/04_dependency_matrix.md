# Dependency Matrix

**Phase:** 3 — Automation & Reliability Mapping
**Requirement:** AUTO-05 (list dependencies for each scraper)
**Date:** 2026-03-19

---

## Summary

Scrapers fall into 4 dependency tiers based on their access method. Shopify JSON API scrapers are the most resilient (structured responses, version-stable). HTML DOM scrapers are the most fragile (CSS selector changes break them silently). Playwright-based scrapers have the heaviest infrastructure requirements.

---

## Python Library Dependencies

| Library | Purpose | Used By | Risk if Unavailable |
|---|---|---|---|
| `requests` | HTTP client for all API/HTML scrapers | All non-Playwright scrapers (~22/24) | Critical — most scrapers non-functional |
| `beautifulsoup4` | HTML parsing | All HTML scrapers (~18/24) | Critical — HTML scrapers non-functional |
| `playwright` | Headless browser for JS-rendered pages | 2-3 scrapers (justpaddles, PB Studio) | High — JS scrapers non-functional |
| `sqlmodel` | ORM for PostgreSQL persistence | All scrapers (data write) | Critical — no data persistence |
| `dlt` | Data load tool / pipeline framework | Pipeline orchestration layer | High — pipeline orchestration breaks |
| `openai` | LLM calls (product enrichment) | Enrichment scripts (not scrapers) | Medium — enrichment offline, core scrape unaffected |
| `lxml` | Optional fast HTML parser backend for BS4 | Some scrapers via BS4 | Low — falls back to html.parser |

---

## External API & Platform Dependencies

| Platform Type | Access Method | Scrapers Affected | API Stability | Fragility |
|---|---|---|---|---|
| **Shopify JSON API** | `GET /products.json?page=N&limit=250` | ~8 scrapers | High (versioned, documented) | Low — JSON structure stable |
| **Nuvemshop / TiendaNube** | HTML DOM scraping | ~6 scrapers | None (no API) | High — CSS selectors break on theme updates |
| **WooCommerce** | HTML DOM scraping | ~4 scrapers | None (no API) | High — same as Nuvemshop |
| **Custom storefronts** | HTML DOM or JS rendering | ~6 scrapers | None | Very High — bespoke DOM, any update breaks |
| **JustPaddles** | Playwright + JS | 1 scraper | None | Very High — JS-heavy, Playwright required |
| **PB Studio** | Playwright + JS | 1 scraper | None | Very High — DNS also isolated in test env |

---

## Infrastructure Dependencies

| Component | Role | Required By | Notes |
|---|---|---|---|
| **PostgreSQL** | Primary data store | All scrapers (write) | Must be running before any scraper executes |
| **Docker** | Container runtime for Playwright | Playwright scrapers | `playwright install chromium` must be run in `backend_v3` container |
| **GitHub Actions** | Pipeline scheduling (CI/CD) | Production pipeline | Workflows: `production-pipeline.yml`, `catalog-weekly-ingestion.yml`, `price-monitoring.yml` |
| **Network / DNS** | HTTP access to stores | All scrapers | Test environment DNS isolation breaks `scrape_propadel.py` and `fetch_pb_studio.py` |

---

## Per-Scraper Dependency Profile

| Scraper Category | requests | beautifulsoup4 | playwright | PostgreSQL | Docker | External Target |
|---|:---:|:---:|:---:|:---:|:---:|---|
| Shopify JSON scrapers (~8) | Yes | No | No | Yes | No | Shopify `/products.json` |
| Nuvemshop/TiendaNube scrapers (~6) | Yes | Yes | No | Yes | No | Store HTML storefront |
| WooCommerce scrapers (~4) | Yes | Yes | No | Yes | No | Store HTML storefront |
| Custom HTML scrapers (~4) | Yes | Yes | No | Yes | No | Custom storefront HTML |
| Playwright scrapers (~2) | No | Yes | Yes | Yes | Yes | JS-rendered storefront |

---

## Dependency Risk Matrix

| Dependency | Change Frequency | Impact of Change | Detection Time | Current Mitigation |
|---|---|---|---|---|
| Shopify `/products.json` schema | Very Low (Shopify API versioned) | High (all Shopify scrapers) | Immediate (parse error) | None |
| Nuvemshop CSS selectors | Medium (theme updates) | High (all Nuvemshop scrapers) | Delayed (silent 0-product run) | None |
| Custom storefront DOM | High (no SLA) | Medium (single scraper) | Delayed (silent 0-product run) | None |
| Playwright / Chromium version | Low | High (all Playwright scrapers) | Immediate (launch error) | Docker image pins version |
| PostgreSQL schema | Low (controlled) | Critical (all scrapers) | Immediate (DB error) | SQLModel migrations |
| GitHub Actions runner | Very Low | High (scheduling) | Immediate (pipeline failure) | GitHub SLA |

---

## Recommendations (for Phase 4 planning)

1. Pin Shopify API version in all Shopify scrapers (e.g., `/products.json?api_version=2024-01`) to prevent silent schema drift.
2. Add per-platform CSS selector version constants in `scraper_utils.py` to centralize fragile selectors.
3. Document Docker image version in `docker-compose.yml` for Playwright scraper reproducibility.
4. Add network connectivity pre-check before scraper runs to distinguish DNS failures from scraper bugs.
