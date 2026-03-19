# Roadmap: SliceInsights v2.0 Workflows & Automation

**Milestone:** v2.0 Workflows & Automation
**Created:** 2026-03-19
**Target:** Complete automation of data pipeline with quality gates, monitoring, and reliable deployments

---

## Phase 5: CI/CD & Testing

**Goal:** Establish automated testing pipeline that validates scrapers on every push to main.

**Requirements:**
- CI-01: GitHub Actions workflow runs on every push to main
- CI-02: Workflow executes unit tests for all scraper modules
- CI-03: Workflow executes smoke tests (audit_data_quality.py) for sample scrapers
- CI-04: Tests must pass before allowing merge to main
- CI-05: Linting/format checks are optional (fail-warn only, not fail-hard)

**Success Criteria:**
1. All new commits to main trigger CI/CD workflow automatically
2. Unit tests run and report pass/fail status
3. Smoke tests validate data pipeline integrity
4. Merge protection requires CI to pass
5. Workflow execution logs are accessible for debugging

**Deliverables:**
- `.github/workflows/ci.yml` — CI/CD workflow definition [DONE — 05-01, commit 3e8307d]
- Unit test suite for scrapers
- Smoke test configuration
- PR protection rules configured

---

## Phase 6: SLO Enforcement & Validation

**Goal:** Implement real-time and scheduled SLO validation to detect quality breaches as they happen.

**Requirements:**
- SLO-01: Real-time SLO validation after each scraper completes
- SLO-02: Scheduled SLO validation job runs 4x daily (every 6 hours)
- SLO-03: Freshness SLO enforced: 24h for Market Offers (prices)
- SLO-04: Completeness SLO enforced: 7 days for Product Master Data (specs)
- SLO-05: SLO validation results logged and queryable for debugging

**Success Criteria:**
1. SLO checks execute both real-time (post-scraper) and scheduled (4x daily)
2. Breaches are detected within 1 hour of occurring
3. SLO status is queryable for alerting systems
4. Validation results include root cause context (which scraper, which metric)
5. Historical logs retained for trend analysis

**Deliverables:**
- `.github/workflows/slo-check.yml` — Scheduled SLO validation
- SLO validation script (Python)
- SLO definition config (24h freshness, 7d completeness)
- Database schema for SLO logs

---

## Phase 7: Alerts & Monitoring

**Goal:** Multi-channel notification system that alerts admins immediately when P1 breaches occur.

**Requirements:**
- ALT-01: Telegram webhook fires when P1 breaches detected (invisible failures, 0 products)
- ALT-02: GitHub Issues created automatically for P1 breaches with remediation context
- ALT-03: Email alerts sent to admin group on P1 SLO breaches
- ALT-04: Alert includes scraper name, breach type, timestamp, last successful run
- ALT-05: Alert contains direct link to RUNBOOK_SCRAPERS.md for troubleshooting

**Success Criteria:**
1. P1 breach triggers all 3 channels (Telegram, GitHub, Email) within 5 minutes
2. Alert message includes actionable context (scraper name, what failed, runbook link)
3. GitHub Issues are deduplicated (no duplicate issues for same breach)
4. Email recipients can be configured per team
5. Alert history is searchable and retained for audit

**Deliverables:**
- Alert notification service (Python)
- Telegram bot integration
- GitHub Issue auto-creation workflow
- Email configuration and templates
- Alert routing logic (P1 vs P2 vs P3)

---

## Phase 8: Deploy & Release Strategy

**Goal:** Implement safe, nightly batch deployments with validation and rollback capability.

**Requirements:**
- DEP-01: Nightly batch job aggregates all successful scraper runs
- DEP-02: Pre-deploy validation runs (freshness check, corruption audit)
- DEP-03: Data published to production database after validation passes
- DEP-04: Deploy workflow includes rollback capability if validation fails
- DEP-05: Deploy log recorded with timestamp, scraper count, data records published

**Success Criteria:**
1. Nightly batch aggregates all successful runs from past 24 hours
2. Pre-deploy validation confirms data integrity before publishing
3. Data is published to production database atomically
4. Failed validation prevents deploy (safe fail)
5. Rollback can restore previous state if needed
6. Each deploy generates audit log

**Deliverables:**
- `.github/workflows/deploy-nightly.yml` — Nightly deploy workflow
- Data aggregation script (Python)
- Pre-deploy validation script
- Database transaction management
- Rollback procedure documentation
- Deploy audit logging

---

## Phase 9: Data Quality Checks & Reporting

**Goal:** Continuous quality monitoring with historical metrics and weekly trend reports.

**Requirements:**
- QC-01: Hourly data quality audit job runs for all 11 active scrapers
- QC-02: Audit measures: freshness, completeness, coverage per scraper
- QC-03: Metrics stored in database for historical trending
- QC-04: Quality dashboard endpoint (HTTP GET) returns current metrics as JSON
- QC-05: Weekly quality report generated showing trends and anomalies
- QC-06: Report highlights which scrapers are degrading or improving

**Success Criteria:**
1. Hourly audit job runs on schedule and captures all 11 scrapers
2. Metrics include freshness, completeness, coverage, timestamp
3. All metrics are persisted for at least 90 days
4. Dashboard endpoint returns metrics in < 500ms
5. Weekly report automatically generated and emailed
6. Report shows scraper trends and highlights anomalies
7. Quality metrics are queryable for debugging

**Deliverables:**
- `.github/workflows/quality-audit.yml` — Hourly quality check
- Quality audit aggregator (Python)
- Dashboard API endpoint
- Database schema for metrics history
- Weekly report generator
- Report templates and styling

---

## Milestone Success Criteria

- [ ] All 26 requirements implemented and tested
- [ ] CI/CD pipeline enforces quality gates
- [ ] Admins receive alerts within 5 minutes of P1 breaches
- [ ] Nightly deployments are safe and auditable
- [ ] Historical quality data enables trend analysis
- [ ] System requires minimal manual intervention
- [ ] All workflows are documented and runbook accessible

---

*Roadmap created: 2026-03-19*
*Phases: 5 (continuing from v1.0 Phase 4)*
*Requirements: 26 total*
