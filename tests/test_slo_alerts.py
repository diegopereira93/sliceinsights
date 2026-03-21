"""
Unit tests for SLOAlertService, dedup functions, channel routing, and message content.

Coverage:
- ALT-01: Telegram P1 message format and send
- ALT-02: GitHub Issues create and dedup (update existing open issue)
- ALT-03: Email P1 send via SMTP STARTTLS
- ALT-04: All channels include scraper_name, metric_type, checked_at, last_record_time
- ALT-05: RUNBOOK_SCRAPERS.md link in all channels
- Routing: P1 -> telegram+github+email; P2 -> telegram+github; P3 -> none
- Graceful degradation: single channel failure doesn't block others
- Dedup: 24h throttle window, first breach, after 24h
- Upsert: creates new / increments existing
- Clear throttle: sets status to "resolved"
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from app.models.slo_alert import SLOAlert, SLOBreach
from app.services.slo_alerts import (
    SLOAlertService,
    should_send_alert,
    upsert_alert_record,
    clear_alert_throttle,
    THROTTLE_HOURS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def p1_breach():
    return SLOBreach(
        scraper_name="mercado_livre",
        metric_type="freshness",
        value_hours=30.5,
        threshold_hours=24.0,
        checked_at="2026-03-19T15:30:45Z",
        last_record_time="2026-03-18T09:00:00Z",
    )


@pytest.fixture
def p2_breach():
    return SLOBreach(
        scraper_name="mercado_livre",
        metric_type="completeness",
        value_hours=200.0,
        threshold_hours=168.0,
        checked_at="2026-03-19T15:30:45Z",
        last_record_time="2026-03-12T09:00:00Z",
    )


@pytest.fixture
def p3_breach():
    return SLOBreach(
        scraper_name="mercado_livre",
        metric_type="coverage",
        value_hours=0.0,
        threshold_hours=0.0,
        checked_at="2026-03-19T15:30:45Z",
        last_record_time=None,
    )


@pytest.fixture
def service():
    return SLOAlertService(
        telegram_token="test-token",
        telegram_chat_id="12345",
        github_token="ghp_test",
        github_repo="owner/repo",
        email_host="smtp.test.com",
        email_port=587,
        email_user="test@test.com",
        email_password="pass",
        admin_email_group="admin1@test.com,admin2@test.com",
    )


@pytest.fixture
def mock_session():
    """Sync session mock (slo_alerts uses synchronous Session)."""
    return MagicMock()


# ---------------------------------------------------------------------------
# Task 1 model tests — verify model/dataclass behaviour
# ---------------------------------------------------------------------------

def test_slo_breach_p1_severity(p1_breach):
    assert p1_breach.severity == "P1"


def test_slo_breach_p2_severity(p2_breach):
    assert p2_breach.severity == "P2"


def test_slo_breach_p3_severity(p3_breach):
    assert p3_breach.severity == "P3"


def test_slo_alert_tablename():
    assert SLOAlert.__tablename__ == "slo_alerts"


# ---------------------------------------------------------------------------
# Telegram tests (ALT-01)
# ---------------------------------------------------------------------------

def test_telegram_p1_send(service, p1_breach):
    """P1 breach sends to Telegram with correct URL and Markdown parse_mode."""
    mock_resp = MagicMock()
    mock_resp.ok = True

    with patch("app.services.slo_alerts.requests.post", return_value=mock_resp) as mock_post:
        result = service._send_telegram(p1_breach)

    assert result is True
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    # Extract URL from positional args
    pos_args = call_kwargs.args if hasattr(call_kwargs, 'args') else call_kwargs[0]
    assert "api.telegram.org" in pos_args[0]
    json_payload = call_kwargs.kwargs.get("json", call_kwargs[1].get("json"))
    assert json_payload["parse_mode"] == "Markdown"
    assert "mercado_livre" in json_payload["text"]
    assert "freshness" in json_payload["text"]
    assert "RUNBOOK_SCRAPERS.md" in json_payload["text"]


def test_telegram_message_contains_required_fields(service, p1_breach):
    """Telegram message text contains all ALT-04 required fields."""
    mock_resp = MagicMock()
    mock_resp.ok = True

    with patch("app.services.slo_alerts.requests.post", return_value=mock_resp) as mock_post:
        service._send_telegram(p1_breach)

    json_payload = mock_post.call_args.kwargs["json"]
    text = json_payload["text"]
    assert "mercado_livre" in text        # scraper_name
    assert "freshness" in text            # metric_type
    assert "2026-03-19T15:30:45Z" in text  # checked_at
    assert "2026-03-18T09:00:00Z" in text  # last_record_time


def test_telegram_no_token_returns_false(p1_breach):
    """When telegram_token is empty, _send_telegram returns False without calling requests."""
    svc = SLOAlertService(telegram_token="", telegram_chat_id="12345")
    with patch("app.services.slo_alerts.requests.post") as mock_post:
        result = svc._send_telegram(p1_breach)
    assert result is False
    mock_post.assert_not_called()


# ---------------------------------------------------------------------------
# GitHub tests (ALT-02)
# ---------------------------------------------------------------------------

def test_github_issue_create(service, p1_breach):
    """When no open issue with matching title exists, create_issue is called."""
    mock_repo = MagicMock()
    mock_repo.get_issues.return_value = []  # No existing issues

    with patch("app.services.slo_alerts.Github") as mock_gh_cls:
        mock_gh = MagicMock()
        mock_gh_cls.return_value = mock_gh
        mock_gh.get_repo.return_value = mock_repo

        result = service._create_or_update_github_issue(p1_breach)

    assert result is True
    mock_repo.create_issue.assert_called_once()
    create_kwargs = mock_repo.create_issue.call_args.kwargs
    assert create_kwargs["title"] == "[P1] mercado_livre SLO Breach: freshness"
    assert "slo-breach" in create_kwargs["labels"]
    assert "p1-critical" in create_kwargs["labels"]


def test_github_issue_dedup(service, p1_breach):
    """When open issue with matching title exists, edit body instead of creating."""
    existing_issue = MagicMock()
    existing_issue.title = "[P1] mercado_livre SLO Breach: freshness"

    mock_repo = MagicMock()
    mock_repo.get_issues.return_value = [existing_issue]

    with patch("app.services.slo_alerts.Github") as mock_gh_cls:
        mock_gh = MagicMock()
        mock_gh_cls.return_value = mock_gh
        mock_gh.get_repo.return_value = mock_repo

        result = service._create_or_update_github_issue(p1_breach)

    assert result is True
    existing_issue.edit.assert_called_once()
    mock_repo.create_issue.assert_not_called()


def test_github_issue_body_contains_runbook(service, p1_breach):
    """GitHub issue body contains RUNBOOK_SCRAPERS.md reference."""
    mock_repo = MagicMock()
    mock_repo.get_issues.return_value = []

    with patch("app.services.slo_alerts.Github") as mock_gh_cls:
        mock_gh = MagicMock()
        mock_gh_cls.return_value = mock_gh
        mock_gh.get_repo.return_value = mock_repo

        service._create_or_update_github_issue(p1_breach)

    body = mock_repo.create_issue.call_args.kwargs["body"]
    assert "RUNBOOK_SCRAPERS.md" in body


def test_github_no_token_returns_false(p1_breach):
    """When github_token is empty, returns False without calling Github."""
    svc = SLOAlertService(github_token="", github_repo="owner/repo")
    with patch("app.services.slo_alerts.Github") as mock_gh:
        result = svc._create_or_update_github_issue(p1_breach)
    assert result is False
    mock_gh.assert_not_called()


# ---------------------------------------------------------------------------
# Email tests (ALT-03)
# ---------------------------------------------------------------------------

def test_email_p1_send(service, p1_breach):
    """P1 breach sends email via SMTP with correct subject and recipients."""
    mock_smtp_instance = MagicMock()
    mock_smtp_ctx = MagicMock()
    mock_smtp_ctx.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.services.slo_alerts.smtplib.SMTP", return_value=mock_smtp_ctx) as mock_smtp:
        result = service._send_email(p1_breach)

    assert result is True
    mock_smtp.assert_called_once_with("smtp.test.com", 587)
    mock_smtp_instance.ehlo.assert_called_once()
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with("test@test.com", "pass")
    mock_smtp_instance.send_message.assert_called_once()

    # Check message subject
    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    assert sent_msg["Subject"] == "[ALERT] mercado_livre freshness SLO breach"


def test_email_body_contains_required_fields(service, p1_breach):
    """Email body contains all ALT-04 required fields."""
    mock_smtp_instance = MagicMock()
    mock_smtp_ctx = MagicMock()
    mock_smtp_ctx.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_ctx.__exit__ = MagicMock(return_value=False)

    with patch("app.services.slo_alerts.smtplib.SMTP", return_value=mock_smtp_ctx):
        service._send_email(p1_breach)

    sent_msg = mock_smtp_instance.send_message.call_args[0][0]
    body = sent_msg.get_body().get_content()
    assert "mercado_livre" in body
    assert "freshness" in body
    assert "2026-03-19T15:30:45Z" in body
    assert "2026-03-18T09:00:00Z" in body
    assert "RUNBOOK_SCRAPERS.md" in body


def test_email_no_host_returns_false(p1_breach):
    """When email_host is empty, returns False without calling smtplib."""
    svc = SLOAlertService(email_host="", email_user="u@test.com", admin_email_group="a@b.com")
    with patch("app.services.slo_alerts.smtplib.SMTP") as mock_smtp:
        result = svc._send_email(p1_breach)
    assert result is False
    mock_smtp.assert_not_called()


# ---------------------------------------------------------------------------
# Routing tests
# ---------------------------------------------------------------------------

def test_p1_routing(service, p1_breach):
    """P1 breach routes to all 3 channels."""
    with patch.object(service, "_send_telegram", return_value=True) as mock_tg, \
         patch.object(service, "_create_or_update_github_issue", return_value=True) as mock_gh, \
         patch.object(service, "_send_email", return_value=True) as mock_em:
        results = service.notify(p1_breach)

    mock_tg.assert_called_once_with(p1_breach)
    mock_gh.assert_called_once_with(p1_breach)
    mock_em.assert_called_once_with(p1_breach)
    assert results == {"telegram": True, "github": True, "email": True}


def test_p2_routing_no_email(service, p2_breach):
    """P2 breach routes to telegram and github only, not email."""
    with patch.object(service, "_send_telegram", return_value=True) as mock_tg, \
         patch.object(service, "_create_or_update_github_issue", return_value=True) as mock_gh, \
         patch.object(service, "_send_email", return_value=True) as mock_em:
        results = service.notify(p2_breach)

    mock_tg.assert_called_once_with(p2_breach)
    mock_gh.assert_called_once_with(p2_breach)
    mock_em.assert_not_called()
    assert "email" not in results
    assert results["telegram"] is True
    assert results["github"] is True


def test_p3_silent(service, p3_breach):
    """P3 breach routes to no channels and returns empty dict."""
    with patch.object(service, "_send_telegram", return_value=True) as mock_tg, \
         patch.object(service, "_create_or_update_github_issue", return_value=True) as mock_gh, \
         patch.object(service, "_send_email", return_value=True) as mock_em:
        results = service.notify(p3_breach)

    mock_tg.assert_not_called()
    mock_gh.assert_not_called()
    mock_em.assert_not_called()
    assert results == {}


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------

def test_graceful_degradation(service, p1_breach):
    """If telegram raises, github and email are still called and results returned."""
    with patch.object(service, "_send_telegram", side_effect=Exception("network error")), \
         patch.object(service, "_create_or_update_github_issue", return_value=True) as mock_gh, \
         patch.object(service, "_send_email", return_value=True) as mock_em:
        results = service.notify(p1_breach)

    assert results["telegram"] is False
    assert results["github"] is True
    assert results["email"] is True
    mock_gh.assert_called_once()
    mock_em.assert_called_once()


# ---------------------------------------------------------------------------
# Content tests (ALT-04, ALT-05)
# ---------------------------------------------------------------------------

def test_breach_payload_fields(service, p1_breach):
    """Every channel includes scraper_name, metric_type, checked_at, last_record_time."""
    # Telegram
    mock_resp = MagicMock()
    mock_resp.ok = True
    with patch("app.services.slo_alerts.requests.post", return_value=mock_resp) as mock_post:
        service._send_telegram(p1_breach)
    text = mock_post.call_args.kwargs["json"]["text"]
    assert "mercado_livre" in text
    assert "freshness" in text
    assert "2026-03-19T15:30:45Z" in text
    assert "2026-03-18T09:00:00Z" in text

    # GitHub
    mock_repo = MagicMock()
    mock_repo.get_issues.return_value = []
    with patch("app.services.slo_alerts.Github") as mock_gh_cls:
        mock_gh_cls.return_value.get_repo.return_value = mock_repo
        service._create_or_update_github_issue(p1_breach)
    body = mock_repo.create_issue.call_args.kwargs["body"]
    assert "mercado_livre" in body
    assert "freshness" in body
    assert "2026-03-19T15:30:45Z" in body
    assert "2026-03-18T09:00:00Z" in body

    # Email
    mock_smtp_instance = MagicMock()
    mock_smtp_ctx = MagicMock()
    mock_smtp_ctx.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_ctx.__exit__ = MagicMock(return_value=False)
    with patch("app.services.slo_alerts.smtplib.SMTP", return_value=mock_smtp_ctx):
        service._send_email(p1_breach)
    email_body = mock_smtp_instance.send_message.call_args[0][0].get_body().get_content()
    assert "mercado_livre" in email_body
    assert "freshness" in email_body
    assert "2026-03-19T15:30:45Z" in email_body
    assert "2026-03-18T09:00:00Z" in email_body


def test_runbook_link_in_all_channels(service, p1_breach):
    """RUNBOOK_SCRAPERS.md appears in telegram message, github body, and email body."""
    # Telegram
    mock_resp = MagicMock()
    mock_resp.ok = True
    with patch("app.services.slo_alerts.requests.post", return_value=mock_resp) as mock_post:
        service._send_telegram(p1_breach)
    assert "RUNBOOK_SCRAPERS.md" in mock_post.call_args.kwargs["json"]["text"]

    # GitHub
    mock_repo = MagicMock()
    mock_repo.get_issues.return_value = []
    with patch("app.services.slo_alerts.Github") as mock_gh_cls:
        mock_gh_cls.return_value.get_repo.return_value = mock_repo
        service._create_or_update_github_issue(p1_breach)
    assert "RUNBOOK_SCRAPERS.md" in mock_repo.create_issue.call_args.kwargs["body"]

    # Email
    mock_smtp_instance = MagicMock()
    mock_smtp_ctx = MagicMock()
    mock_smtp_ctx.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_ctx.__exit__ = MagicMock(return_value=False)
    with patch("app.services.slo_alerts.smtplib.SMTP", return_value=mock_smtp_ctx):
        service._send_email(p1_breach)
    email_body = mock_smtp_instance.send_message.call_args[0][0].get_body().get_content()
    assert "RUNBOOK_SCRAPERS.md" in email_body


# ---------------------------------------------------------------------------
# Dedup / throttle tests
# ---------------------------------------------------------------------------

def test_dedup_first_breach(mock_session):
    """When no dedup record exists, should_send_alert returns True."""
    mock_session.exec.return_value.first.return_value = None
    assert should_send_alert(mock_session, "mercado_livre", "freshness") is True


def test_dedup_throttle_24h(mock_session):
    """When active record with last_alert_time < 24h ago, should_send_alert returns False."""
    record = SLOAlert(
        scraper_name="mercado_livre",
        metric_type="freshness",
        last_alert_time=datetime.now(timezone.utc) - timedelta(hours=1),
        status="active",
    )
    mock_session.exec.return_value.first.return_value = record
    assert should_send_alert(mock_session, "mercado_livre", "freshness") is False


def test_dedup_after_24h(mock_session):
    """When active record with last_alert_time > 24h ago, should_send_alert returns True."""
    record = SLOAlert(
        scraper_name="mercado_livre",
        metric_type="freshness",
        last_alert_time=datetime.now(timezone.utc) - timedelta(hours=25),
        status="active",
    )
    mock_session.exec.return_value.first.return_value = record
    assert should_send_alert(mock_session, "mercado_livre", "freshness") is True


def test_clear_throttle(mock_session):
    """clear_alert_throttle sets record status to 'resolved'."""
    record = SLOAlert(
        scraper_name="mercado_livre",
        metric_type="freshness",
        last_alert_time=datetime.now(timezone.utc),
        status="active",
    )
    mock_session.exec.return_value.first.return_value = record
    clear_alert_throttle(mock_session, "mercado_livre", "freshness")
    assert record.status == "resolved"
    mock_session.add.assert_called_once_with(record)
    mock_session.commit.assert_called_once()


def test_upsert_creates_new(mock_session):
    """upsert_alert_record creates new SLOAlert when none exists."""
    mock_session.exec.return_value.first.return_value = None
    upsert_alert_record(mock_session, "shopee", "freshness")
    mock_session.add.assert_called_once()
    added = mock_session.add.call_args[0][0]
    assert isinstance(added, SLOAlert)
    assert added.scraper_name == "shopee"
    assert added.metric_type == "freshness"
    assert added.alert_count == 1
    assert added.status == "active"
    mock_session.commit.assert_called_once()


def test_upsert_updates_existing(mock_session):
    """upsert_alert_record increments alert_count and updates last_alert_time."""
    old_time = datetime.now(timezone.utc) - timedelta(hours=26)
    record = SLOAlert(
        scraper_name="shopee",
        metric_type="freshness",
        last_alert_time=old_time,
        status="active",
        alert_count=3,
    )
    mock_session.exec.return_value.first.return_value = record
    upsert_alert_record(mock_session, "shopee", "freshness")
    assert record.alert_count == 4
    assert record.last_alert_time > old_time
    mock_session.add.assert_called_once_with(record)
    mock_session.commit.assert_called_once()


def test_throttle_hours_constant():
    """THROTTLE_HOURS is 24."""
    assert THROTTLE_HOURS == 24
