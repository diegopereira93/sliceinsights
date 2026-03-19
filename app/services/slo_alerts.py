"""
SLO Alert Service.

Multi-channel alert service for SLO breaches: Telegram, GitHub Issues, and Email.
Includes 24-hour deduplication throttle via the slo_alerts table.
"""

import os
import logging
import smtplib
import ssl
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage

import requests
from github import Github, Auth
from sqlmodel import Session, select

from app.models.slo_alert import SLOAlert, SLOBreach

logger = logging.getLogger(__name__)

THROTTLE_HOURS = 24

RUNBOOK_URL = "https://github.com/{repo}/blob/main/docs/RUNBOOK_SCRAPERS.md"


def _get_runbook_url() -> str:
    repo = os.getenv("GITHUB_REPOSITORY", "sliceinsights/sliceinsights")
    return RUNBOOK_URL.format(repo=repo)


# ---------------------------------------------------------------------------
# Dedup / throttle functions (module-level for easier testing)
# ---------------------------------------------------------------------------

def should_send_alert(session: Session, scraper_name: str, metric_type: str) -> bool:
    """Return True if this breach should trigger alerts (not throttled)."""
    stmt = select(SLOAlert).where(
        SLOAlert.scraper_name == scraper_name,
        SLOAlert.metric_type == metric_type,
        SLOAlert.status == "active",
    )
    record = session.exec(stmt).first()
    if record is None:
        return True  # First breach — always send
    cutoff = datetime.now(timezone.utc) - timedelta(hours=THROTTLE_HOURS)
    last = record.last_alert_time
    # Normalise to aware datetime for comparison
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return last < cutoff


def upsert_alert_record(session: Session, scraper_name: str, metric_type: str) -> None:
    """Create or update the dedup record after an alert is sent."""
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
            alert_count=1,
        )
        session.add(record)
    else:
        record.last_alert_time = now
        record.alert_count += 1
        record.updated_at = now
        session.add(record)
    session.commit()


def clear_alert_throttle(session: Session, scraper_name: str, metric_type: str) -> None:
    """Mark an alert record as resolved (clears the throttle for next breach)."""
    stmt = select(SLOAlert).where(
        SLOAlert.scraper_name == scraper_name,
        SLOAlert.metric_type == metric_type,
    )
    record = session.exec(stmt).first()
    if record is None:
        return
    record.status = "resolved"
    record.updated_at = datetime.now(timezone.utc)
    session.add(record)
    session.commit()


# ---------------------------------------------------------------------------
# SLOAlertService
# ---------------------------------------------------------------------------

class SLOAlertService:
    """Dispatch SLO breach alerts to Telegram, GitHub Issues, and/or Email."""

    def __init__(
        self,
        telegram_token: str = "",
        telegram_chat_id: str = "",
        github_token: str = "",
        github_repo: str = "",
        email_host: str = "",
        email_port: int = 587,
        email_user: str = "",
        email_password: str = "",
        admin_email_group: str = "",
    ):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.github_token = github_token
        self.github_repo = github_repo
        self.email_host = email_host
        self.email_port = email_port
        self.email_user = email_user
        self.email_password = email_password
        self.admin_email_group = admin_email_group

    def notify(self, breach: SLOBreach) -> dict[str, bool]:
        """Fan out to all channels for the breach severity. Returns per-channel result."""
        channels = self._get_channels_for_severity(breach.severity)
        results: dict[str, bool] = {}
        for channel in channels:
            try:
                results[channel] = self._send(channel, breach)
            except Exception as exc:
                logger.warning("Alert channel %s failed: %s", channel, exc)
                results[channel] = False
        return results

    def _get_channels_for_severity(self, severity: str) -> list[str]:
        if severity == "P1":
            return ["telegram", "github", "email"]
        elif severity == "P2":
            return ["telegram", "github"]
        return []

    def _send(self, channel: str, breach: SLOBreach) -> bool:
        if channel == "telegram":
            return self._send_telegram(breach)
        elif channel == "github":
            return self._create_or_update_github_issue(breach)
        elif channel == "email":
            return self._send_email(breach)
        return False

    def _send_telegram(self, breach: SLOBreach) -> bool:
        if not self.telegram_token or not self.telegram_chat_id:
            return False

        icon = "\U0001f6a8" if breach.severity == "P1" else "\u26a0\ufe0f"
        runbook_url = _get_runbook_url()
        message = (
            f"{icon} *SLO Breach -- {breach.severity}*\n\n"
            f"*Scraper:* {breach.scraper_name}\n"
            f"*Metric:* {breach.metric_type}\n"
            f"*Age:* {breach.value_hours:.1f}h (threshold: {breach.threshold_hours:.0f}h)\n"
            f"*Last data:* {breach.last_record_time or 'unknown'}\n"
            f"*Detected:* {breach.checked_at}\n\n"
            f"[Runbook]({runbook_url})"
        )
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        resp = requests.post(
            url,
            json={
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
            },
            timeout=15,
        )
        return resp.ok

    def _create_or_update_github_issue(self, breach: SLOBreach) -> bool:
        if not self.github_token or not self.github_repo:
            return False

        g = Github(auth=Auth.Token(self.github_token))
        repo = g.get_repo(self.github_repo)

        title = f"[{breach.severity}] {breach.scraper_name} SLO Breach: {breach.metric_type}"
        runbook_url = _get_runbook_url()
        body = (
            f"## SLO Breach Detected\n\n"
            f"**Scraper:** {breach.scraper_name}\n"
            f"**Metric:** {breach.metric_type}\n"
            f"**Severity:** {breach.severity}\n"
            f"**Age:** {breach.value_hours:.1f}h (threshold: {breach.threshold_hours:.0f}h)\n"
            f"**Last data:** {breach.last_record_time or 'unknown'}\n"
            f"**Detected:** {breach.checked_at}\n\n"
            f"## Remediation\n\n"
            f"1. Check scraper logs for errors\n"
            f"2. Verify data pipeline is running\n"
            f"3. Confirm database connectivity\n"
            f"4. Re-run scraper if needed\n\n"
            f"## Runbook\n\n"
            f"See: {runbook_url} (RUNBOOK_SCRAPERS.md)\n"
        )

        if breach.severity == "P1":
            labels = ["slo-breach", "p1-critical"]
        else:
            labels = ["slo-breach", "p2-important"]

        # Search for existing open issue with same title
        open_issues = repo.get_issues(state="open", labels=["slo-breach"])
        for issue in open_issues:
            if issue.title == title:
                issue.edit(body=body)
                return True

        repo.create_issue(title=title, body=body, labels=labels)
        return True

    def _send_email(self, breach: SLOBreach) -> bool:
        if not self.email_host or not self.email_user or not self.admin_email_group:
            return False

        recipients = [r.strip() for r in self.admin_email_group.split(",") if r.strip()]
        runbook_url = _get_runbook_url()
        subject = f"[ALERT] {breach.scraper_name} freshness SLO breach"
        body_text = (
            f"SLO Breach Alert\n"
            f"================\n\n"
            f"Scraper:      {breach.scraper_name}\n"
            f"Metric:       {breach.metric_type}\n"
            f"Severity:     {breach.severity}\n"
            f"Age:          {breach.value_hours:.1f}h (threshold: {breach.threshold_hours:.0f}h)\n"
            f"Last data:    {breach.last_record_time or 'unknown'}\n"
            f"Detected:     {breach.checked_at}\n\n"
            f"Runbook: {runbook_url}\n"
            f"(RUNBOOK_SCRAPERS.md)\n"
        )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.email_user
        msg["To"] = ", ".join(recipients)
        msg.set_content(body_text)

        with smtplib.SMTP(self.email_host, self.email_port) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(self.email_user, self.email_password)
            smtp.send_message(msg)

        return True


def get_slo_alert_service() -> SLOAlertService:
    """Return a configured SLOAlertService from environment variables."""
    return SLOAlertService(
        telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        github_token=os.getenv("GITHUB_TOKEN", ""),
        github_repo=os.getenv("GITHUB_REPOSITORY", ""),
        email_host=os.getenv("EMAIL_HOST", ""),
        email_port=int(os.getenv("EMAIL_PORT", "587")),
        email_user=os.getenv("EMAIL_USER", ""),
        email_password=os.getenv("EMAIL_PASSWORD", ""),
        admin_email_group=os.getenv("ADMIN_EMAIL_GROUP", ""),
    )
