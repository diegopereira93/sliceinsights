# Phase 7: Alerts & Monitoring - Research

**Researched:** 2026-03-19
**Domain:** Multi-channel alerting (Telegram Bot API, PyGithub, smtplib), PostgreSQL deduplication
**Confidence:** HIGH

## Summary

Phase 7 builds a multi-channel notification system that fires immediately after SLO validation detects P1/P2 breaches. The alert worker queries the existing `slo_logs` table for new `fail` entries, applies a 24-hour throttle via a new `slo_alerts` table, then fans out to up to three channels (Telegram, GitHub Issues, Email) based on severity routing rules decided in CONTEXT.md.

The project already contains `app/services/price_alerts.py`, which is the canonical pattern for Telegram messaging. All three channels use Python standard library or lightweight client libraries already available in the ecosystem. The most critical implementation detail is graceful degradation: each channel send must be isolated so one failure never blocks the others.

**Primary recommendation:** Adapt `PriceAlertService` into a new `SLOAlertService` class in `app/services/slo_alerts.py`, add a `scripts/alert_worker.py` CLI entrypoint, and extend `.github/workflows/slo-check.yml` with a follow-up `alert` job step that runs after slo_validator completes.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Real-time alerts: triggered immediately after SLO validation (slo_validator.py) detects and writes breach logs
- Separate alert worker queries slo_logs table for newly-failed entries (status=FAIL)
- No delay; alert sends within seconds of breach detection during SLO check cycle (every 6 hours)
- **P1 (Critical):** Freshness SLO breach → Telegram + GitHub Issues + Email
- **P2 (Important):** Completeness SLO breach → Telegram + GitHub Issues only
- **P3 (Informational):** Coverage gaps → logs only (no alert sent)
- Dedup key: composite of `scraper_name` + `metric_type`
- First breach: alert immediately; subsequent occurrences: silence for 24 hours; re-alert after 24h if still unresolved
- Resolution: When SLO returns to PASS, clear throttle; new FAIL resets window
- Dedup state tracked via `slo_alerts` table
- GitHub Issue deduplication: search for existing open issue with same scraper + metric; update body instead of creating new
- Email recipients via env var `ADMIN_EMAIL_GROUP` (comma-separated or single distribution list)
- Every alert must include direct link to `docs/RUNBOOK_SCRAPERS.md`
- Timestamp format: ISO 8601 with UTC timezone (`2026-03-19T15:30:45Z`)

### Claude's Discretion
- Exact email template HTML/CSS
- GitHub Issue label colors and emoji choices
- Telegram message formatting details (Markdown vs plain)
- Alert history retention policy (query window for "last 30 days" reports)
- Retry logic for failed channel sends (e.g., if Telegram API times out)

### Deferred Ideas (OUT OF SCOPE)
- Slack integration
- Metrics dashboard/portal (belongs in Phase 9)
- PagerDuty integration
- Alert aggregation window (batching multiple P2 alerts)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ALT-01 | Telegram webhook fires when P1 breaches detected | Existing `price_alerts.py` Telegram pattern reusable directly; `requests.post` to Bot API with `parse_mode=Markdown` |
| ALT-02 | GitHub Issues created automatically for P1 breaches with remediation context | PyGithub 2.8.1 `repo.create_issue()` + `repo.get_issues(state='open', labels=['slo-breach'])` for dedup search |
| ALT-03 | Email alerts sent to admin group on P1 SLO breaches | `smtplib.SMTP` with STARTTLS on port 587; `email.message.EmailMessage` for construction |
| ALT-04 | Alert includes scraper name, breach type, timestamp, last successful run | Available in `slo_logs.details` JSONB: `scraper_name`, `metric_type`, `checked_at`, `details.newest_record` |
| ALT-05 | Alert contains direct link to RUNBOOK_SCRAPERS.md for troubleshooting | Hardcoded relative path `docs/RUNBOOK_SCRAPERS.md` embedded in all message templates |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | 2.31.0 (in requirements.txt) | Telegram Bot API HTTP calls | Already installed; existing pattern in price_alerts.py |
| PyGithub | 2.8.1 (latest) | GitHub Issues API — create, search, update | Official Python GitHub client; stable API |
| smtplib | stdlib | Send email via SMTP | Python standard library; no install needed |
| email.message | stdlib | Construct EmailMessage objects | Python standard library; modern API |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlmodel | 0.0.14 (in requirements.txt) | Query slo_logs, write slo_alerts | Same ORM used by slo_validator.py |
| python-dotenv | 1.0.0 (in requirements.txt) | Load env vars in CLI context | For local dev; GitHub Actions uses secrets |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| requests (Telegram) | httpx | httpx already in requirements.txt but requests is already used in price_alerts.py — stay consistent |
| smtplib | sendgrid, mailgun | Third-party services cost money and add a credential; smtplib + any SMTP relay is self-contained |
| PyGithub | GitHub REST API via requests | PyGithub handles pagination, auth headers, and type safety; worth the dependency |

**Installation:**
```bash
pip install PyGithub==2.8.1
```
(All other libraries already in requirements.txt)

**Version verification:** PyGithub 2.8.1 confirmed as latest via `pip index versions PyGithub`.

---

## Architecture Patterns

### Recommended Project Structure
```
app/
└── services/
    └── slo_alerts.py        # SLOAlertService class (Telegram + GitHub + Email channels)

scripts/
└── alert_worker.py          # CLI entrypoint: query slo_logs → deduplicate → dispatch

app/models/
└── slo_alert.py             # SLOAlert ORM model (slo_alerts table)

tests/
└── test_slo_alerts.py       # Unit tests with mocked channels
```

### Pattern 1: SLOAlertService — Channel Fan-out with Graceful Degradation

**What:** Each channel send is wrapped in its own try/except. The service collects results and logs failures without raising exceptions.

**When to use:** All multi-channel notification scenarios where one channel failing must not prevent others.

**Example:**
```python
# Source: adapted from app/services/price_alerts.py
class SLOAlertService:
    def notify(self, breach: SLOBreach) -> dict[str, bool]:
        results = {}
        channels = self._get_channels_for_severity(breach.severity)
        for channel in channels:
            try:
                results[channel] = self._send(channel, breach)
            except Exception as exc:
                logger.warning(f"[alert] {channel} failed: {exc}")
                results[channel] = False
        return results

    def _get_channels_for_severity(self, severity: str) -> list[str]:
        if severity == "P1":
            return ["telegram", "github", "email"]
        elif severity == "P2":
            return ["telegram", "github"]
        return []  # P3: log only, no channels
```

### Pattern 2: Deduplication via slo_alerts Table

**What:** Before sending any alert, query `slo_alerts` for the (scraper_name, metric_type) composite key. Check `last_alert_time`. Only send if no record exists or `last_alert_time` is more than 24 hours ago.

**When to use:** Every alert dispatch in the worker.

**Example:**
```python
# Source: PostgreSQL upsert pattern (HIGH confidence — standard SQL)
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from app.models.slo_alert import SLOAlert

THROTTLE_HOURS = 24

def should_send_alert(session: Session, scraper_name: str, metric_type: str) -> bool:
    stmt = select(SLOAlert).where(
        SLOAlert.scraper_name == scraper_name,
        SLOAlert.metric_type == metric_type,
        SLOAlert.status == "active",
    )
    record = session.exec(stmt).first()
    if record is None:
        return True  # First occurrence
    cutoff = datetime.now(timezone.utc) - timedelta(hours=THROTTLE_HOURS)
    return record.last_alert_time < cutoff

def upsert_alert_record(session: Session, scraper_name: str, metric_type: str) -> None:
    stmt = select(SLOAlert).where(
        SLOAlert.scraper_name == scraper_name,
        SLOAlert.metric_type == metric_type,
    )
    record = session.exec(stmt).first()
    now = datetime.now(timezone.utc)
    if record is None:
        record = SLOAlert(
            scraper_name=scraper_name,
            metric_type=metric_type,
            last_alert_time=now,
            status="active",
        )
        session.add(record)
    else:
        record.last_alert_time = now
        record.status = "active"
    session.commit()

def clear_alert_throttle(session: Session, scraper_name: str, metric_type: str) -> None:
    """Call when SLO returns to PASS — clears throttle so next FAIL re-alerts immediately."""
    stmt = select(SLOAlert).where(
        SLOAlert.scraper_name == scraper_name,
        SLOAlert.metric_type == metric_type,
    )
    record = session.exec(stmt).first()
    if record:
        record.status = "resolved"
        session.commit()
```

### Pattern 3: GitHub Issue Deduplication

**What:** Before creating a new issue, search open issues with label `slo-breach` and match title prefix `[P1] {scraper_name}` or `[P2] {scraper_name}`. If found, update the body with latest timestamp. If not found, create new.

**Example:**
```python
# Source: PyGithub 2.8.1 official docs (HIGH confidence)
from github import Github

def get_or_create_issue(repo, title: str, body: str, labels: list[str]):
    # Search open issues for this scraper+metric combo
    open_issues = repo.get_issues(state="open", labels=["slo-breach"])
    for issue in open_issues:
        if issue.title == title:
            issue.edit(body=body)  # Update with latest breach details
            return issue, False    # (issue, was_created)
    new_issue = repo.create_issue(title=title, body=body, labels=labels)
    return new_issue, True
```

### Pattern 4: Telegram Message Formatting

**What:** Use `parse_mode=Markdown` (same as price_alerts.py). P1 gets `🚨`, P2 gets `⚠️`. Include scraper name, metric, age, threshold, timestamp, and runbook link.

**Example:**
```python
# Source: adapted from app/services/price_alerts.py (HIGH confidence — existing project code)
RUNBOOK_URL = "https://github.com/{owner}/{repo}/blob/main/docs/RUNBOOK_SCRAPERS.md"

def _format_telegram_message(breach) -> str:
    icon = "🚨" if breach.severity == "P1" else "⚠️"
    return (
        f"{icon} *SLO Breach — {breach.severity}*\n\n"
        f"*Scraper:* {breach.scraper_name}\n"
        f"*Metric:* {breach.metric_type}\n"
        f"*Age:* {breach.value_hours:.1f}h (threshold: {breach.threshold_hours:.0f}h)\n"
        f"*Last data:* {breach.last_record_time or 'unknown'}\n"
        f"*Detected:* {breach.checked_at}\n\n"
        f"[Runbook]({RUNBOOK_URL})"
    )
```

### Pattern 5: Email with smtplib + STARTTLS

**What:** Use `smtplib.SMTP` on port 587 with `starttls()`. Construct message with `email.message.EmailMessage`. Parse `ADMIN_EMAIL_GROUP` env var as comma-separated list.

**Example:**
```python
# Source: Python stdlib docs — smtplib (HIGH confidence)
import smtplib
import ssl
from email.message import EmailMessage

def send_email_alert(breach, recipients: list[str], smtp_host: str, smtp_port: int,
                     smtp_user: str, smtp_password: str) -> bool:
    msg = EmailMessage()
    msg["Subject"] = f"[ALERT] {breach.scraper_name} freshness SLO breach"
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)
    msg.set_content(_format_email_body(breach))  # plain text fallback
    msg.add_alternative(_format_email_html(breach), subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
    return True
```

### Anti-Patterns to Avoid
- **Raising exceptions in channel sends:** If Telegram fails, GitHub and Email must still run. Always catch per-channel.
- **Creating a new GitHub Issue on every alert cycle:** Search for existing open issue first; update body if found.
- **Querying all slo_logs on every worker run:** Use `checked_at > last_run_time` filter. Store worker cursor or use a `processed` flag.
- **Blocking SLO workflow on alert failure:** Alert worker runs as a separate step with `continue-on-error: true`.
- **Hardcoding recipients:** Always read from `ADMIN_EMAIL_GROUP` env var.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| GitHub API authentication + HTTP calls | Custom requests wrapper | PyGithub 2.8.1 | Handles auth headers, rate limit retries, pagination, typed responses |
| Telegram message delivery | Custom HTTP client | `requests.post` (already in price_alerts.py) | Pattern already proven; no new dependency |
| Email TLS negotiation | Manual socket/SSL code | `smtplib.SMTP` + `starttls()` | stdlib handles TLS certificate validation via `ssl.create_default_context()` |
| Alert deduplication state | In-memory dict / file | `slo_alerts` PostgreSQL table | Persists across worker restarts, queryable for debugging, already have DB connection |

**Key insight:** The entire notification stack maps to stdlib + one new PyPI library (PyGithub). The project already has all other dependencies.

---

## Common Pitfalls

### Pitfall 1: slo_logs has no "processed" marker
**What goes wrong:** Alert worker re-processes old FAIL entries on every run, sending duplicate alerts.
**Why it happens:** `slo_logs` has no `alert_sent` column; worker has no cursor.
**How to avoid:** Use `slo_alerts.last_alert_time` as the dedup gate. The throttle window (24h) is the cursor. Alternatively, filter `slo_logs` by `checked_at > (now - 6h)` since the workflow runs every 6 hours.
**Warning signs:** Telegram receiving identical alerts minutes apart.

### Pitfall 2: GitHub Issue labels must pre-exist
**What goes wrong:** `repo.create_issue(labels=["p1-critical"])` raises `GithubException` if label doesn't exist in the repo.
**Why it happens:** GitHub API rejects unknown label names (422 error).
**How to avoid:** Wave 0 task — create labels `slo-breach`, `p1-critical`, `p2-important` in the repo before the alert worker runs. Or use `repo.get_label()` with a try/create fallback.
**Warning signs:** `GithubException: 422 Unprocessable Entity` on first issue creation.

### Pitfall 3: Telegram Markdown escaping
**What goes wrong:** Characters like `-`, `.`, `(`, `)` in scraper names or URLs break Markdown v2 rendering; messages arrive malformed or are silently dropped.
**Why it happens:** Telegram's `MarkdownV2` mode requires escaping many characters. `Markdown` (v1) is more lenient.
**How to avoid:** Stick with `parse_mode=Markdown` (v1) as already used in `price_alerts.py`. Avoid special characters in the message that aren't inside backtick or asterisk blocks.
**Warning signs:** Telegram returns `{"ok": false, "error_code": 400, "description": "Bad Request: can't parse entities"}`.

### Pitfall 4: SMTP App Passwords
**What goes wrong:** Gmail/Outlook reject the account password when logging in from smtplib.
**Why it happens:** Google and Microsoft require App Passwords for third-party SMTP access when 2FA is enabled.
**How to avoid:** Document in env var setup that `EMAIL_PASSWORD` must be an App Password, not the account password. Alternatively, use a transactional SMTP relay (SendGrid free tier, AWS SES) with a dedicated API key.
**Warning signs:** `smtplib.SMTPAuthenticationError: 535 Authentication failed`.

### Pitfall 5: slo_alerts table missing before first run
**What goes wrong:** `alert_worker.py` fails with `psycopg2.errors.UndefinedTable` on first execution.
**Why it happens:** No migration created for `slo_alerts` table yet.
**How to avoid:** Wave 0 plan task must include Alembic migration for `slo_alerts` table before the worker code runs.
**Warning signs:** Worker crashes on first GitHub Actions run after deploy.

---

## Database Design

### slo_alerts Table (new — deduplication state)

```python
# app/models/slo_alert.py
class SLOAlert(SQLModel, table=True):
    __tablename__ = "slo_alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    scraper_name: str = Field(index=True)      # e.g. "mercado_livre"
    metric_type: str                            # "freshness" | "completeness"
    last_alert_time: datetime                   # UTC — used for 24h throttle
    status: str = Field(default="active")       # "active" | "resolved"
    alert_count: int = Field(default=1)         # How many times alerted for this breach
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Unique constraint:** `(scraper_name, metric_type)` — one row per scraper-metric pair, upserted on each alert.

### slo_logs Query Pattern (reading Phase 6 output)

```python
# Source: slo_validator.py schema (HIGH confidence — existing code)
from datetime import datetime, timezone, timedelta

def get_recent_failures(session: Session, lookback_hours: int = 7) -> list[SLOLog]:
    """Fetch FAIL entries written in the last lookback_hours window."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    stmt = (
        select(SLOLog)
        .where(SLOLog.status == "fail")
        .where(SLOLog.checked_at >= cutoff)
        .order_by(SLOLog.checked_at.desc())
    )
    return list(session.exec(stmt).all())
```

Note: `slo_logs.checked_at` uses `datetime.utcnow()` (naive), so compare against naive UTC datetime in queries.

---

## Integration Architecture

```
.github/workflows/slo-check.yml
  ├── job: slo-check          (existing — runs slo_validator.py --all)
  └── job: alert              (NEW — runs after slo-check, continue-on-error: true)
        └── python scripts/alert_worker.py --all

scripts/alert_worker.py
  ├── query slo_logs for recent FAIL entries (last 7h window)
  ├── for each FAIL:
  │     ├── determine severity (freshness→P1, completeness→P2)
  │     ├── check slo_alerts for throttle (24h gate)
  │     ├── if should_send:
  │     │     ├── dispatch SLOAlertService.notify(breach)
  │     │     └── upsert slo_alerts record
  │     └── if PASS (for resolution detection): clear_alert_throttle()
  └── exit 0 (never raises; workflow continues regardless)

app/services/slo_alerts.py
  ├── SLOAlertService.notify(breach) → dict[channel, bool]
  ├── _send_telegram(breach) → bool
  ├── _create_or_update_github_issue(breach) → bool
  └── _send_email(breach) → bool
```

**GitHub Actions dependency:**
```yaml
jobs:
  slo-check:
    # existing job
  alert:
    needs: slo-check
    if: always()   # run even if slo-check fails
    continue-on-error: true
    steps:
      - run: python scripts/alert_worker.py --all
        env:
          DATABASE_URL_SYNC: ${{ secrets.DATABASE_URL_SYNC }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ADMIN_EMAIL_GROUP: ${{ secrets.ADMIN_EMAIL_GROUP }}
          EMAIL_HOST: ${{ secrets.EMAIL_HOST }}
          EMAIL_PORT: ${{ secrets.EMAIL_PORT }}
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `smtplib.SMTP_SSL` port 465 | `smtplib.SMTP` + `starttls()` port 587 | ~2015 onwards | STARTTLS is now recommended; port 587 is standard submission port |
| PyGithub 1.x (`github.Github`) | PyGithub 2.x (`github.Auth.Token`) | PyGithub 2.0 (2023) | Auth constructor changed; use `github.Auth.Token(token)` not positional arg |
| Telegram `parse_mode=MarkdownV2` | Stick with `parse_mode=Markdown` | Telegram Bot API 4.5+ | MarkdownV2 requires heavy escaping; v1 Markdown is simpler and sufficient |

**Deprecated/outdated:**
- `Github(token)` positional constructor (PyGithub 1.x): replaced by `Github(auth=Auth.Token(token))` in 2.x
- `SMTP_SSL` on port 465: still works but STARTTLS on 587 is the modern standard

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (detected in tests/conftest.py + tests/*.py) |
| Config file | none — no pytest.ini/pyproject.toml found; pytest discovers via convention |
| Quick run command | `PYTHONPATH=. pytest tests/test_slo_alerts.py -x -q` |
| Full suite command | `PYTHONPATH=. pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ALT-01 | Telegram send called with correct P1 message and format | unit | `PYTHONPATH=. pytest tests/test_slo_alerts.py::test_telegram_p1_send -x` | Wave 0 |
| ALT-02 | GitHub Issue created; existing open issue updated not duplicated | unit | `PYTHONPATH=. pytest tests/test_slo_alerts.py::test_github_issue_dedup -x` | Wave 0 |
| ALT-03 | Email send called with correct subject/recipients for P1 | unit | `PYTHONPATH=. pytest tests/test_slo_alerts.py::test_email_p1_send -x` | Wave 0 |
| ALT-04 | Alert payload contains scraper_name, breach_type, timestamp, last_record_time | unit | `PYTHONPATH=. pytest tests/test_slo_alerts.py::test_breach_payload_fields -x` | Wave 0 |
| ALT-05 | RUNBOOK_SCRAPERS.md link present in Telegram, GitHub, Email messages | unit | `PYTHONPATH=. pytest tests/test_slo_alerts.py::test_runbook_link_in_all_channels -x` | Wave 0 |
| dedup | 24h throttle prevents second alert within window | unit | `PYTHONPATH=. pytest tests/test_slo_alerts.py::test_dedup_throttle_24h -x` | Wave 0 |
| routing | P2 breach sends to Telegram+GitHub only, not Email | unit | `PYTHONPATH=. pytest tests/test_slo_alerts.py::test_p2_routing_no_email -x` | Wave 0 |
| routing | P3 breach sends to no channels | unit | `PYTHONPATH=. pytest tests/test_slo_alerts.py::test_p3_silent -x` | Wave 0 |

**Testing strategy:** All channel sends are tested with `unittest.mock.patch` / `MagicMock`. No live Telegram/GitHub/email calls in CI. Database interactions use the existing `mock_session` fixture pattern from `tests/conftest.py`.

### Sampling Rate
- **Per task commit:** `PYTHONPATH=. pytest tests/test_slo_alerts.py -x -q`
- **Per wave merge:** `PYTHONPATH=. pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_slo_alerts.py` — covers ALT-01 through ALT-05, dedup, routing (all new)
- [ ] `app/models/slo_alert.py` — SLOAlert ORM model (needed before tests can import it)
- [ ] Alembic migration for `slo_alerts` table — must exist before integration tests or live runs
- [ ] GitHub repo labels `slo-breach`, `p1-critical`, `p2-important` — manual one-time setup; document in plan

---

## Open Questions

1. **RUNBOOK_SCRAPERS.md URL form**
   - What we know: File exists at `docs/RUNBOOK_SCRAPERS.md`; must be linked in every alert
   - What's unclear: Should the link be a GitHub raw URL, a GitHub blob URL, or a relative path? Telegram and email need absolute URLs; GitHub Issue bodies can use relative paths.
   - Recommendation: Use `https://github.com/{GITHUB_REPOSITORY}/blob/main/docs/RUNBOOK_SCRAPERS.md`. Read `GITHUB_REPOSITORY` env var (auto-set by GitHub Actions) or fall back to a hardcoded constant.

2. **slo_logs.checked_at timezone awareness**
   - What we know: `checked_at = Field(default_factory=datetime.utcnow)` produces naive UTC datetimes
   - What's unclear: Queries comparing naive vs aware datetimes may warn or fail depending on SQLAlchemy version
   - Recommendation: In `alert_worker.py` use naive UTC cutoff (`datetime.utcnow() - timedelta(hours=7)`) to match the column type, or add `timezone=True` to the column in a migration.

3. **SMTP relay choice**
   - What we know: smtplib + STARTTLS works with any SMTP server; env vars `EMAIL_HOST/PORT/USER/PASSWORD` control it
   - What's unclear: Which SMTP relay the operator will configure (Gmail, SendGrid, SES, self-hosted)
   - Recommendation: Document that `EMAIL_HOST=smtp.gmail.com`, `EMAIL_PORT=587` works for Gmail with an App Password. Add to docs/ci-setup.md or RUNBOOK.

---

## Sources

### Primary (HIGH confidence)
- `app/services/price_alerts.py` — Existing Telegram integration pattern (requests.post, parse_mode=Markdown, timeout=15)
- `scripts/slo_validator.py` — slo_logs schema, status values ("fail"/"pass"/"skip"), `checked_at` field type
- `app/models/slo.py` — SLOLog ORM model: scraper_name, metric_type, value_hours, threshold_hours, status, checked_at, details (JSONB)
- `.github/workflows/slo-check.yml` — Existing workflow structure to extend with alert job
- `tests/conftest.py` — Existing mock patterns (mock_session, MagicMock) for test architecture

### Secondary (MEDIUM confidence)
- [PyGithub Issues documentation](https://pygithub.readthedocs.io/en/latest/examples/Issue.html) — `repo.create_issue()`, `repo.get_issues(state='open', labels=[...])`, `issue.edit(body=...)` patterns
- [Python smtplib docs](https://docs.python.org/3/library/smtplib.html) — STARTTLS pattern, `ssl.create_default_context()`, `send_message()`
- PyGithub 2.8.1 latest confirmed via `pip index versions PyGithub`

### Tertiary (LOW confidence)
- Web search: PyGithub 2.x auth constructor change (`Auth.Token`) — not directly verified against official changelog; flag for confirmation during implementation

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified in project requirements.txt or pip registry
- Architecture: HIGH — based directly on existing slo_validator.py and price_alerts.py code patterns
- Pitfalls: MEDIUM — GitHub label pre-existence and SMTP auth issues verified via web search + official docs; Telegram Markdown escaping from price_alerts.py pattern
- Dedup strategy: HIGH — standard PostgreSQL upsert on existing ORM stack

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable libraries; Telegram Bot API and PyGithub are low churn)
