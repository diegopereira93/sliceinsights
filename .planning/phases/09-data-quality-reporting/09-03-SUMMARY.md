---
phase: 09-data-quality-reporting
plan: 03
subsystem: quality-reporting
tags: [quality-report, email, github-actions]
requires: [QC-05, QC-06]
provides: [weekly_report_generator, weekly_report_workflow]
affects: [scripts/quality_report.py, .github/workflows/quality-report.yml]
tech_stack:
  added: [pandas, smtplib]
  patterns: [html-email, anomaly-detection, weekly-cron]
key_files:
  created:
    - path: scripts/quality_report.py
      description: Weekly quality report generator with HTML email
    - path: tests/test_quality_report.py
      description: Unit tests for report generation
    - path: .github/workflows/quality-report.yml
      description: Weekly report workflow (Monday 08:00 UTC)
key_decisions:
  - Anomaly detection uses >10% threshold for flagging scrapers
  - Report uses pandas for week-over-week calculations
  - HTML email with green (#dcfce7) improving and red (#fee2e2) degrading sections
  - Arrow indicators for trend visualization
  - Email sent via smtplib with HTML alternative (same as SLOAlertService)
requirements_completed: [QC-05, QC-06]
duration: 10 min
completed: 2026-03-20T18:55:00Z
---

# Phase 9 Plan 3: Weekly Quality Report Generator Summary

**Objective:** Create the weekly quality report generator and its GitHub Actions workflow.

## What Was Built

**Report Generator (quality_report.py):**
- `fetch_weekly_data()`: Queries 4 weeks of quality_metrics data
- `detect_anomalies()`: Flags scrapers with >10% change week-over-week
- `build_weekly_report()`: Generates HTML with:
  - Degrading section (red #fee2e2)
  - Improving section (green #dcfce7)
  - 4-week trend table with ↑/↓ arrows
- `send_report()`: Sends HTML email via smtplib with starttls
- CLI: `--reference-date`, `--dry-run`

**Weekly Workflow (quality-report.yml):**
- Runs Monday 08:00 UTC (`cron: '0 8 * * 1'`)
- workflow_dispatch for manual triggering
- Email secrets injection (ADMIN_EMAIL_GROUP, EMAIL_HOST, etc.)

## Deviations from Plan

None - plan executed exactly as written.

## Files Modified

- scripts/quality_report.py (created)
- tests/test_quality_report.py (created)
- .github/workflows/quality-report.yml (created)

## Test Results

9 tests passing:
- test_detect_anomalies_improving
- test_detect_anomalies_degrading
- test_detect_anomalies_no_anomalies
- test_build_weekly_report_contains_table
- test_build_weekly_report_contains_improving
- test_build_weekly_report_contains_degrading
- test_send_report_with_mocked_smtp
- test_send_report_returns_false_when_no_config
- test_fetch_weekly_data_empty

## Next

Phase 9 complete — ready for verification.
