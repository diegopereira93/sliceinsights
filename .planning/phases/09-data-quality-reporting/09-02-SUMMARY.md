---
phase: 09-data-quality-reporting
plan: 02
subsystem: quality-reporting
tags: [quality-dashboard, api, github-actions]
requires: [QC-01, QC-04]
provides: [quality_dashboard_api, quality_audit_workflow]
affects: [app/api/endpoints/quality.py, app/api/routes.py, .github/workflows/quality-audit.yml]
tech_stack:
  added: [fastapi, cachetools]
  patterns: [ttlcache, async-endpoint, matrix-workflow]
key_files:
  created:
    - path: app/api/endpoints/quality.py
      description: Quality dashboard endpoint with TTLCache
    - path: tests/test_quality_dashboard.py
      description: Unit tests for dashboard endpoint
    - path: .github/workflows/quality-audit.yml
      description: Hourly quality audit workflow
  modified:
    - path: app/api/routes.py
      description: Added quality router registration
key_decisions:
  - Used cachetools TTLCache (ttl=300) for 5-min dashboard caching
  - Global status thresholds: healthy=0 fail, degraded=1-2 fail, critical=3+ fail
  - Matrix workflow with 11 scrapers and fail-fast:false
  - Consolidate job runs with if:always() to ensure completion even on partial failures
requirements_completed: [QC-01, QC-04]
duration: 10 min
completed: 2026-03-20T18:45:00Z
---

# Phase 9 Plan 2: Quality Dashboard API & Hourly Audit Workflow Summary

**Objective:** Create the quality dashboard API endpoint and the hourly quality-audit GitHub Actions workflow.

## What Was Built

**Dashboard Endpoint (`GET /api/quality/dashboard`):**
- Returns JSON with status, scrapers array, and summary object
- Uses 5-minute TTLCache to avoid DB pressure
- Queries latest metrics per scraper using `DISTINCT ON (scraper_name)`
- Classifies global status: healthy (0 fail), degraded (1-2 fail), critical (3+ fail)

**Hourly Quality Audit Workflow:**
- Runs every hour via cron (`0 * * * *`)
- Matrix strategy with 11 scrapers in parallel
- `fail-fast: false` to ensure all scrapers run even if one fails
- `continue-on-error: true` on audit job
- Consolidation job runs after all matrix jobs (`if: always()`)
- Injects `DATABASE_URL_SYNC` and `GITHUB_RUN_ID` via secrets

## Deviations from Plan

None - plan executed exactly as written.

## Files Modified

- app/api/endpoints/quality.py (created)
- app/api/routes.py (added quality router)
- tests/test_quality_dashboard.py (created)
- .github/workflows/quality-audit.yml (created)

## Test Results

6 tests passing:
- test_dashboard_returns_healthy_status
- test_dashboard_returns_degraded_status
- test_dashboard_returns_critical_status
- test_dashboard_response_shape
- test_dashboard_scraper_object_keys
- test_dashboard_empty_db

## Next

Ready for 09-03: Weekly Quality Report Generator.
