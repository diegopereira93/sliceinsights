---
phase: 09-data-quality-reporting
plan: 01
subsystem: quality-reporting
tags: [quality-metrics, alembic, cli]
requires: [QC-02, QC-03]
provides: [quality_metric_model, quality_aggregator_cli, alembic_migration]
affects: [app/models/quality_metric.py, app/db/database.py, alembic/env.py, scripts/quality_aggregator.py]
tech_stack:
  added: [sqlmodel, alembic]
  patterns: [sqlmodel-table, jsonb-columns, composite-index]
key_files:
  created:
    - path: app/models/quality_metric.py
      description: QualityMetric SQLModel with 5 metric columns + run_id + JSONB details
    - path: scripts/quality_aggregator.py
      description: CLI for computing and persisting quality metrics
    - path: alembic/versions/add_quality_metrics.py
      description: Alembic migration for quality_metrics table
    - path: tests/test_quality_aggregator.py
      description: Unit tests for compute/persist/consolidate
  modified:
    - path: app/db/database.py
      description: Added QualityMetric import registration
    - path: alembic/env.py
      description: Added QualityMetric import for autogenerate
key_decisions:
  - Used JSONB for details column to store flexible metadata
  - Composite index on (scraper_name, checked_at desc) for dashboard query performance
  - Used timedelta for _hours_ago to avoid datetime.replace edge cases
requirements_completed: [QC-02, QC-03]
duration: 15 min
completed: 2026-03-20T18:35:00Z
---

# Phase 9 Plan 1: Quality Metric Model & Aggregator Summary

**Objective:** Create the QualityMetric data model, Alembic migration, and quality_aggregator.py CLI that computes and persists per-scraper quality metrics.

## What Was Built

QualityMetric SQLModel stores one row per scraper per workflow run with:
- `scraper_name`: Index for filtering
- `run_id`: GITHUB_RUN_ID for incident correlation
- `freshness_hours`: Hours since newest MarketOffer.last_updated
- `completeness_pct`: % products with all required fields filled
- `coverage_pct`: % required fields filled across all products
- `product_count`: Total active products for this scraper
- `error_rate`: Fraction of runs in last 24h that failed
- `status`: "pass" or "fail" based on thresholds
- `checked_at`: Timestamp with default factory
- `details`: JSONB column for flexible metadata

The quality_aggregator.py CLI provides:
- `compute_metrics(scraper_name, session)`: Computes all 5 metrics
- `persist_metrics(...)`: Inserts QualityMetric row
- `compute_and_persist(...)`: Convenience function combining both
- `consolidate(run_id, session)`: Aggregates all metrics for a run

CLI arguments:
- `--scraper NAME`: Target single scraper
- `--all`: Iterate all active scrapers from market_offers
- `--consolidate`: Consolidate results for this run

## Deviations from Plan

None - plan executed exactly as written.

## Files Modified

- app/models/quality_metric.py (created)
- app/db/database.py (added QualityMetric import)
- alembic/env.py (added QualityMetric import)
- alembic/versions/add_quality_metrics.py (created)
- scripts/quality_aggregator.py (created)
- tests/test_quality_aggregator.py (created)

## Test Results

4 tests passing:
- test_compute_metrics_returns_dict_shape
- test_persist_metrics_inserts_row
- test_consolidate_queries_by_run_id
- test_compute_metrics_no_offers

## Next

Ready for 09-02: Quality Dashboard API and Hourly Audit Workflow.
