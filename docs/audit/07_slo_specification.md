# SLO Specification: Data Freshness

**Phase:** 3 — Automation & Reliability Mapping
**Requirement:** AUTO-04 (establish SLOs for data freshness)
**Date:** 2026-03-19

---

## Summary

Two distinct data classes with different freshness requirements are defined. Market Offers (prices, availability) change frequently and require daily refresh. Product Master Data (specs, descriptions) changes infrequently and requires weekly or on-demand refresh. Current infrastructure has no enforcement mechanism for either SLO — `measure_freshness.py` can measure age but does not trigger alerts or pipeline runs.

---

## Data Class Definitions

### Class 1: Market Offers (Prices & Availability)

| Attribute | Value |
|---|---|
| Table | `market_offers` (or equivalent price/availability table) |
| Data elements | Current price, sale price, availability status, stock level |
| Change frequency | High — prices change daily or more frequently (promotions, restock) |
| Business impact of staleness | High — stale prices cause incorrect recommendations and user trust loss |
| **Freshness SLO** | **Refreshed within 24 hours** |
| Measurement | `measure_freshness.py` calculates age of `MarketOffer` records |

### Class 2: Product Master Data (Specs & Catalog)

| Attribute | Value |
|---|---|
| Table | `products` / `product_specs` (or equivalent catalog table) |
| Data elements | Product name, description, specifications, images, category |
| Change frequency | Low — new products added weekly; specs rarely change post-launch |
| Business impact of staleness | Medium — missing new products; outdated specs less critical than wrong prices |
| **Freshness SLO** | **Refreshed within 7 days** (or on-demand when new products detected) |
| Measurement | Last ingestion timestamp per product record |

---

## SLO Table

| SLO ID | Data Class | Target | Measurement Method | Current Status | Enforcement |
|---|---|---|---|---|---|
| SLO-PRICE-01 | Market Offers (prices) | 100% of records refreshed within 24h | `measure_freshness.py` age calculation | Measured, not enforced | **None** |
| SLO-SPEC-01 | Product Master Data (specs) | 100% of records refreshed within 7 days | Last ingestion timestamp | Not measured | **None** |
| SLO-AVAIL-01 | Availability / stock status | 100% of records refreshed within 24h | Same as SLO-PRICE-01 | Measured, not enforced | **None** |

---

## Current State vs Target

| Metric | Current State | Target State |
|---|---|---|
| Freshness measurement | `measure_freshness.py` calculates age of records | Same tool, with alerting threshold |
| Freshness alerting | None | Alert if any store's records exceed SLO age |
| Pipeline scheduling | GitHub Actions workflows (daily/weekly cadence) | Same cadence, with SLO verification post-run |
| SLO breach response | None — no detection | Automatic re-run or human alert |
| Historical freshness tracking | None | Log freshness metrics per run to `pipeline_runs` table |

---

## Pipeline Schedule Alignment

The existing GitHub Actions workflows align with the proposed SLOs:

| Workflow | Cadence | SLO Alignment |
|---|---|---|
| `price-monitoring.yml` | Daily (inferred from name) | Satisfies SLO-PRICE-01 if all scrapers succeed |
| `catalog-weekly-ingestion.yml` | Weekly | Satisfies SLO-SPEC-01 if all scrapers succeed |
| `production-pipeline.yml` | On-demand / scheduled | General pipeline; SLO coverage depends on what it runs |

**Gap:** Pipeline success today = scraper exits 0. It does not verify that the SLO was actually satisfied (i.e., records were written and are fresh). A scraper that exits 0 with 0 products written still marks the workflow as green.

---

## SLO Breach Scenarios

| Scenario | SLO Breached | Current Detection | Proposed Detection |
|---|---|---|---|
| Scraper crashes (exit 1) | Yes | GitHub Actions failure notification | Same |
| Scraper exits 0 with 0 products (CSS break) | Yes | **None** | Post-run count validation |
| Scraper writes data but DB connection drops mid-batch | Yes | **None** | DB write confirmation logging |
| GitHub Actions workflow not triggered (cron missed) | Yes | **None** | Freshness age alert from `measure_freshness.py` |
| Store's prices not updated in source (store-side stale) | No (not our SLO) | N/A | N/A |

---

## Measurement Infrastructure

`measure_freshness.py` exists and calculates record age. To enforce SLOs, it needs two additions:

1. **Threshold parameter:** Accept `--max-age-hours 24` and exit non-zero if any store's records exceed the threshold.
2. **Per-store breakdown:** Report freshness per store (not just aggregate) to identify which stores are breaching SLO.

This would allow GitHub Actions to fail the workflow when SLO is breached, triggering the existing failure notification path.

---

## Recommendations (for Phase 4 planning)

1. Add `--max-age-hours` flag to `measure_freshness.py` — exit 1 if any store breaches SLO-PRICE-01 (24h). Run this as a final step in `price-monitoring.yml`.
2. Add per-store freshness output to `measure_freshness.py` to pinpoint which stores are stale.
3. Add a `product_catalog_age` measurement script (parallel to `measure_freshness.py`) for SLO-SPEC-01 (7-day).
4. Store freshness metrics in a `pipeline_health` table per run to enable trend analysis and SLO compliance reporting.
5. Define an error budget: tolerate up to 2 SLO-PRICE-01 breaches per week per store before escalating to engineering.
