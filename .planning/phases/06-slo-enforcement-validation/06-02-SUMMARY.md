---
phase: 6
plan: "06-02"
subsystem: slo-enforcement
tags: [slo, validation, freshness, completeness, sqlmodel]
dependency_graph:
  requires: [06-01]
  provides: [scripts/slo_validator.py, check_freshness, check_completeness, validate_job_slo]
  affects: [slo_logs table, Phase 7 alerts]
tech_stack:
  added: []
  patterns: [sync SQLModel session, argparse CLI, non-blocking real-time hook]
key_files:
  created:
    - scripts/slo_validator.py
  modified: []
decisions:
  - "Use store_name (not a separate scraper_name column) as the grouping key for freshness — matches MarketOffer model"
  - "Completeness accepts scraper_name param for API symmetry but always checks global paddle_master catalog"
  - "Infinite age (no data) stored as 99999.0 hours in value_hours to keep column numeric; reason=no_data in details JSON"
  - "validate_job_slo is non-blocking — SLO check failure never halts scraper ingestion"
metrics:
  duration: "~10 minutes"
  completed_date: "2026-03-19"
  tasks_completed: 4
  files_created: 1
---

# Phase 6 Plan 02: SLO Validation Engine Summary

SLO validation engine with freshness (24h) and completeness (168h) checks backed by slo_logs persistence and a non-blocking real-time hook.

## What Was Built

`scripts/slo_validator.py` — single module with four entry points:

| Symbol | Purpose |
|--------|---------|
| `check_freshness(session, scraper_name=None)` | Groups `market_offers` by `store_name`, compares `max(last_updated)` age to `FRESHNESS_SLO_HOURS=24`, writes one `SLOLog` per store |
| `check_completeness(session, scraper_name=None)` | Queries `max(paddle_master.updated_at)`, compares to `COMPLETENESS_SLO_HOURS=168`, writes one `SLOLog` |
| `validate_job_slo(scraper_name)` | Non-blocking real-time hook for scrapers — wraps freshness check in try/except |
| `main() / CLI` | `--all` runs both checks for all stores; `--scraper NAME` filters to one store |

## Tasks Completed

| # | Task | Commit |
|---|------|--------|
| 1 | Shell + DB session (`init_db_sync`, `sync_engine`) | 291fb9a |
| 2 | `check_freshness` with `last_updated`, per-store grouping, slo_logs writes | 291fb9a |
| 3 | `check_completeness` with `updated_at`, global catalog check, slo_logs writes | 291fb9a |
| 4 | CLI `--all`/`--scraper` + `validate_job_slo` real-time hook | 291fb9a |

## Edge Cases Handled

- **No data**: logs `fail` with `details={"reason": "no_data"}`, stores `value_hours=99999.0`
- **NULL / naive timestamps**: `_make_aware()` attaches UTC before comparison
- **Scraper filter**: `scraper_name=None` checks all stores; non-None filters `WHERE store_name = ?`
- **Non-blocking hook**: `validate_job_slo` wraps in try/except — scraper exits 0 regardless

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

**Note:** The plan referenced `product_specs` table and `scraper_name` column on `MarketOffer`. Neither exists in the actual models. `check_freshness` groups by `store_name` (the actual field on `MarketOffer`) and `check_completeness` uses `paddle_master` directly (the actual catalog table). This matches the research doc and model definitions.

## Self-Check: PASSED

- `scripts/slo_validator.py` exists: FOUND
- Commit 291fb9a exists: FOUND
- `check_freshness` defined: FOUND
- `check_completeness` defined: FOUND
- `validate_job_slo` defined: FOUND
- CLI `--all` / `--scraper` args: FOUND
- Writes to `slo_logs` via `SLOLog`: FOUND
