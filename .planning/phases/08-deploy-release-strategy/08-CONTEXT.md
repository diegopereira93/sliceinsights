# Phase 8: Deploy & Release Strategy - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement safe, nightly batch deployments that aggregate data from all active scrapers, validate for quality and integrity, publish atomically to production, and provide zero-downtime rollback capability. Data flows: scraper runs → SLO validation → staging table → pre-deploy validation → production (versioned) → queryable deploy logs.

</domain>

<decisions>
## Implementation Decisions

### Data Aggregation Scope
- **SLO-gated publishing:** Only data from scrapers that pass SLO checks (freshness 24h, completeness 7d) are included in the nightly batch. Scrapers with breached SLOs are held for the next batch/manual intervention.
- **Fixed calendar window:** Aggregate data updated between 12 AM and 12 AM UTC (calendar day), not rolling 24h. Predictable for operators and audit logs.
- **Partial batches accepted:** If 5 of 11 scrapers pass SLO, publish those 5. Do not block all 11 waiting for broken scrapers.
- **Upsert semantics:** Duplicate paddles (same ID across batches) use last-write-wins upsert. Most recent data overwrites previous.
- **Deploy log detail:** Log both summary (X scrapers passed, Y products published) AND detailed per-scraper table (scraper name, SLO status, product count, timestamp).

### Pre-Deploy Validation Strategy
- **Dual validation:** Before publishing to prod, run both SLO re-validation (freshness/completeness check) AND corruption audit (schema integrity, NULL validation, record count sanity).
- **Validation gates deployment:** If validation fails (SLO breach or corruption detected), deployment is blocked. Data remains in staging table.
- **Staging table retention:** Failed batches sit in staging for operator action. Not discarded.
- **Operator-controlled retry:** Operator can retry validation without manual debugging. Command: `deploy --validate-batch <batch_id>` re-runs validation and reports.
- **Force-publish override:** If operator is confident failure is a false positive (e.g., validation script bug), `--force-publish <batch_id>` is available. Forces publish, logged with timestamp and operator ID, triggers alert to team.

### Rollback & Safe Publishing
- **Atomic transaction:** Publish via single ACID transaction: `SELECT FROM staging, INSERT/UPDATE prod, COMMIT`. All-or-nothing atomicity.
- **Version-based rollback:** Flag-based versioning for zero-downtime rollback. New data marked `version_id=N`, old `version_id=N-1` marked inactive. Rollback = flip flags back (instant).
- **Schema migration:** Add `version_id INTEGER` and `is_active BOOLEAN` columns to `market_offers` and `paddle_master` tables in Phase 8. All publishes tag rows with version.
- **Version retention:** Keep current + 1 previous version active only. After new batch succeeds, delete old versions. Prevents unbounded storage growth.
- **Rollback mechanics:** Post-publish, if issue detected, operator runs `deploy --rollback <batch_id>`. Flips flags, instant recovery, no downtime. Keeps new version in DB for audit.

### Deployment Timing & Orchestration
- **Event-driven, not fixed schedule:** Deploy does NOT run on cron (not a fixed time). Triggered by webhook after scraper suite completes.
- **Webhook trigger:** After all GitHub Actions CI jobs finish (last scraper completes), webhook fires: `POST /deploy/trigger`. Deploy immediately begins aggregation.
- **Strict scraper requirement:** Deploy waits for ALL 11 active scrapers to have completed and passed SLO validation. No proceeding with partial coverage (e.g., 8/11).
- **Configurable timeout:** Max wait time before deploy gives up: 2-3 hours (configurable per environment). If timeout expires and not all 11 have run, abort deployment and alert operator via Telegram/Slack.
- **Failure scenario:** If a scraper hangs/fails to complete within timeout, deploy aborts. Operator investigates scraper logs and manually fixes. Can retry deploy via webhook re-trigger or manual CLI.

### Claude's Discretion
- Exact alarm/timeout thresholds in deploy logic (within 2-3h window)
- Webhook retry logic (how many retries if scraper webhook fires but data incomplete)
- Batch aggregation query optimization (indexes, query plan)
- Staging table cleanup (TTL for old staging batches)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Specifications
- `.planning/REQUIREMENTS.md` — DEP-01 through DEP-05 (nightly batch, validation, publish, rollback, audit log)
- `.planning/ROADMAP.md` (Phase 8 section) — Phase boundary, success criteria, deliverables list

### Prior Phase Context
- `.planning/phases/06-slo-enforcement-validation/06-CONTEXT.md` — SLO validation logic (freshness 24h, completeness 7d), SLOLog schema
- `.planning/phases/07-alerts-and-monitoring/07-CONTEXT.md` — Alert channels (Telegram, GitHub Issues, Email), notification patterns

### Architecture & Code
- `scripts/run_scraper.py` — Unified scraper entry point with post-run SLO hook (`finish_run`)
- `scripts/scraper_utils.py` — `finish_run()` implementation, SLO validation integration
- `app/db/database.py` — Sync/async engine setup, SQLModel integration, migration patterns
- `app/models/slo.py` — SLOLog ORM model, schema definition
- `.github/workflows/ci.yml` — Current CI workflow (unit/smoke tests); deploy workflow will integrate here
- `.github/workflows/slo-check.yml` — Existing SLO validation workflow; deploy workflow follows this pattern

### Data Quality & Audit
- `docs/slo-guide.md` — SLO enforcement architecture, schema, runbook
- `docs/operations/RUNBOOK_SCRAPERS.md` — Scraper troubleshooting guide (linked in alerts)
- `docs/AUDIT_REPORT.md` — Baseline audit findings (6 of 11 scrapers passing, known failure modes)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`run_scraper.py`:** Entry point for individual scraper runs. Deploy aggregation will query SLO logs from runs invoked via this script.
- **`scraper_utils.finish_run()`:** Non-blocking SLO validation hook. Already integrated; deploy validation will build on SLOLog data created here.
- **`slo_validator.py` (`check_freshness`, `check_completeness`):** Validation logic exists. Pre-deploy validation can reuse these functions.
- **`alert_worker.py` and `SLOAlertService`:** Multi-channel notification patterns (Telegram, GitHub, Email). Deploy notifications will follow same pattern.

### Established Patterns
- **Webhook-triggered workflows:** Phase 7 (alerts) already uses GitHub Actions workflows. Deploy workflow will follow same GitHub Actions pattern.
- **Database transactions:** FastAPI async queries use SQLModel sessions. Sync scripts use SQLAlchemy Core for atomic operations. Deploy aggregation will follow sync pattern (batch job context).
- **Logging to SLOLog table:** All scraper runs write SLOLog entries. Deploy will query this table to determine which scrapers passed SLO.

### Integration Points
- **SLO logs table:** Deploy queries `slo_logs` to determine SLO status per scraper. This is the source of truth for "did scraper pass?"
- **GitHub Actions:** Deploy workflow will be defined in `.github/workflows/deploy-nightly.yml`, integrated into CI pipeline after slo-check job.
- **Database:** Deploy needs access to both `market_offers` and `paddle_master` tables for aggregation, plus new `version_id` / `is_active` columns (schema migration).
- **Staging table:** New `market_offers_staging` table for holding aggregated batch before validation and publish.
- **Webhook endpoint:** Deploy needs HTTP endpoint to receive "scrapers done" webhook. May be internal GitHub Actions → API, or standalone trigger endpoint.

</code_context>

<specifics>
## Specific Ideas

- **Webhook source:** GitHub Actions job that runs after final scraper job completes. Can use GitHub's native webhook context or a dedicated GitHub App.
- **Batch ID tracking:** Each deploy batch assigned unique ID (timestamp + hash, e.g., `batch_20260319_2f4a8`). Used in logs, rollback commands, audit trail.
- **Operator tools:** CLI commands for operators: `deploy --validate-batch <id>`, `deploy --force-publish <id>`, `deploy --rollback <id>`. Clear error messages, detailed logs.
- **Slack/Telegram integration:** Deploy start/failure notifications follow Phase 7 pattern. Success notifications include batch summary (scraper count, product count, version ID).
- **Database credentials:** Deploy job needs `DATABASE_URL_SYNC` secret (existing in GitHub Actions from Phase 6). Reuse existing pattern.

</specifics>

<deferred>
## Deferred Ideas

- **Multi-environment deployments (staging → prod):** Approval gates, promote-on-success. Deferred to v2.1.
- **Automated retry of failed batches:** Currently manual operator retries. Auto-retry with exponential backoff could be Phase 9 enhancement.
- **Metrics and dashboard for deploy history:** Deploy logs queryable from dashboard. Phase 9 (Quality & Reporting) may include this.
- **Canary deployments:** Publish to subset of stores first, then full fleet. Too complex for v2.0; keep nightly batch all-or-nothing.

</deferred>

---

*Phase: 08-deploy-release-strategy*
*Context gathered: 2026-03-19*
