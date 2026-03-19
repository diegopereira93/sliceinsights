# Phase 7: Alerts & Monitoring - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Multi-channel notification system that triggers when P1 SLO breaches occur. Sends alerts via Telegram, GitHub Issues, and Email with actionable context (scraper name, breach type, timestamp, last successful run, runbook link). Deduplicates alerts and retains audit history for debugging.

Integration point: Receives breach signals from Phase 6 (SLO validation); feeds into Phase 8 (deployments) and Phase 9 (reporting).

</domain>

<decisions>
## Implementation Decisions

### Alert Trigger Mechanism
- Real-time alerts: triggered immediately after SLO validation (slo_validator.py) detects and writes breach logs
- Separate alert worker queries slo_logs table for newly-failed entries (status=FAIL)
- No delay; alert sends within seconds of breach detection during SLO check cycle (every 6 hours)

### P1/P2/P3 Severity Classification
- **P1 (Critical):** Freshness SLO breach (market_offers not updated within 24h)
  - Indicates no price data flow → recommender engine gets stale data
  - Triggers all 3 alert channels (Telegram, GitHub, Email)
- **P2 (Important):** Completeness SLO breach (paddle_master specs not updated within 7d)
  - Indicates missing product specifications → recommendation quality degrades
  - Triggers Telegram + GitHub Issues only
- **P3 (Informational):** Coverage gaps (fewer scrapers than baseline)
  - Logged but not alerted (reduces noise)

### Alert Deduplication & Throttling
- **First breach occurrence:** Alert sends immediately (no throttle)
- **Subsequent occurrences:** If breach persists, silence alerts for 24 hours
- **After 24h:** Re-alert if breach still unresolved
- **Dedup key:** Composite of `scraper_name` + `metric_type` (freshness/completeness/coverage)
- **Resolution:** When SLO returns to PASS, clear throttle; new FAIL resets throttle window
- **Track via:** slo_alerts table (scraper_name, metric_type, last_alert_time, status)

### Channel Routing & Message Format
- **Telegram:** All P1 + P2 breaches; format: scraper name, metric, threshold, actual value, runbook link
  - Icon: 🚨 for P1, ⚠️ for P2
  - Include clickable link to docs/RUNBOOK_SCRAPERS.md
- **GitHub Issues:** All P1 + P2 breaches; auto-created with:
  - Title: `[P1/P2] {scraper_name} SLO Breach: {metric_type}`
  - Body: timestamp, value, threshold, last successful run time, remediation steps
  - Label: `slo-breach` + severity label (`p1-critical`, `p2-important`)
  - Deduplication: search for open issue with same scraper + metric; update instead of creating new
- **Email:** P1 breaches only; sends to admin group with:
  - Subject: `[ALERT] {scraper_name} freshness SLO breach`
  - Body: summary + actionable context + direct link to runbook
  - Recipients: configured via env var `ADMIN_EMAIL_GROUP` (single distribution list or comma-separated)

### Claude's Discretion
- Exact email template HTML/CSS
- GitHub Issue label colors and emoji choices
- Telegram message formatting details (markdown vs plain)
- Alert history retention policy (query window for "last 30 days" reports)
- Retry logic for failed channel sends (e.g., if Telegram API times out)

</decisions>

<specifics>
## Specific Ideas

- **RUNBOOK_SCRAPERS.md integration:** Every alert must include direct link to runbook with anchor to scraper-specific troubleshooting section
- **Timestamp format:** Use ISO 8601 with UTC timezone in all alerts (e.g., `2026-03-19T15:30:45Z`)
- **Pattern to reuse:** `app/services/price_alerts.py` already has multi-channel notification pattern (Telegram + webhook); adapt for SLO alerts
- **Low-noise approach:** P3 (coverage gaps) intentionally silent to avoid alert fatigue; operator can query slo_logs if needed

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### SLO Enforcement & Integration
- `.planning/ROADMAP.md` — Phase 6 output (slo_logs table schema, freshness/completeness definitions)
- `.planning/REQUIREMENTS.md` — ALT-01 through ALT-05 requirements defining alert channels and content
- `docs/slo-guide.md` — SLO validation architecture, scheduler, database schema, breach detection logic

### Existing Alert Patterns
- `app/services/price_alerts.py` — Multi-channel notification service (Telegram + webhook); reusable pattern for message formatting and API calls
- `docs/features/price-alerts/price-alerts-spec.md` — Feature spec showing Telegram message structure

### Scraper Documentation
- `docs/RUNBOOK_SCRAPERS.md` — Troubleshooting guide for each of 24 scrapers; referenced in every alert

### Database & Models
- `.planning/phases/06-slo-enforcement-validation/06-SUMMARY.md` — SLO validator implementation details, slo_logs table structure
- `app/models/` — ORM models for slo_logs, paddle_master, market_offers tables

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/services/price_alerts.py` — Multi-channel notification service with Telegram and webhook patterns; can adapt `PriceAlertService` class structure for SLO alerts
- GitHub Actions workflow pattern in `.github/workflows/slo-check.yml` — Can extend to add alert job step after slo_validator.py completes
- `scripts/slo_validator.py` — Outputs slo_logs table entries; alert worker can subscribe to FAIL status entries

### Established Patterns
- **Telegram integration:** Using requests.post() to Telegram Bot API with auth token from env var (pattern already in price_alerts.py)
- **Database logging:** SLO validator already logs to PostgreSQL; alert dedup state can live in same database (new slo_alerts table or column in slo_logs)
- **GitHub Actions scheduling:** Existing 6-hour cron in slo-check.yml; alert job can run as follow-up step

### Integration Points
- **SLO validation output:** Alert worker queries slo_logs where status='FAIL' and created_at > last_check_time
- **Configuration:** Environment variables for credentials (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, GITHUB_TOKEN, ADMIN_EMAIL_GROUP, EMAIL_HOST, EMAIL_PORT)
- **Error handling:** Should gracefully degrade if one channel fails (e.g., email server down) without blocking other channels

</code_context>

<deferred>
## Deferred Ideas

- **Slack integration** — Additional channel beyond Telegram/GitHub/Email; can be added in future phase
- **Metrics dashboard/portal** — Visual SLO status page for operations team; belongs in Phase 9 (Data Quality & Reporting)
- **PagerDuty integration** — On-call escalation for critical breaches; future enhancement
- **Alert aggregation window** — Batching multiple P2 alerts into single message when burst occurs; defer until alert fatigue detected in production

</deferred>

---

*Phase: 07-alerts-monitoring*
*Context gathered: 2026-03-19*
