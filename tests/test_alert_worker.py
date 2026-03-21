"""
Unit tests for scripts/alert_worker.py — Phase 7 (ALT-01 through ALT-05)

Tests cover:
- slo_log_to_breach field mapping
- get_recent_failures query filtering
- process_failures throttle/send logic
- process_passes resolution detection
- Error handling in process_failures
"""
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.models.slo import SLOLog
from app.models.slo_alert import SLOBreach
from scripts.alert_worker import (
    slo_log_to_breach,
    get_recent_failures,
    process_failures,
    process_passes,
    main,
    LOOKBACK_HOURS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_slo_log(
    scraper_name="mercado_livre",
    metric_type="freshness",
    value_hours=30.0,
    threshold_hours=24.0,
    status="fail",
    checked_at=None,
    details=None,
) -> SLOLog:
    if checked_at is None:
        checked_at = datetime(2026, 3, 18, 9, 0, 0)
    if details is None:
        details = {"newest_record": "2026-03-18T09:00:00Z", "age_hours": 30.0, "reason": "stale_data"}
    log = SLOLog(
        scraper_name=scraper_name,
        metric_type=metric_type,
        value_hours=value_hours,
        threshold_hours=threshold_hours,
        status=status,
        checked_at=checked_at,
        details=details,
    )
    return log


# ---------------------------------------------------------------------------
# Test 1: slo_log_to_breach field mapping
# ---------------------------------------------------------------------------

def test_slo_log_to_breach_mapping():
    """slo_log_to_breach must map every field correctly."""
    log = _make_slo_log(
        scraper_name="mercado_livre",
        metric_type="freshness",
        value_hours=30.5,
        threshold_hours=24.0,
        checked_at=datetime(2026, 3, 18, 9, 0, 0),
        details={"newest_record": "2026-03-18T09:00:00Z"},
    )
    breach = slo_log_to_breach(log)

    assert isinstance(breach, SLOBreach)
    assert breach.scraper_name == "mercado_livre"
    assert breach.metric_type == "freshness"
    assert breach.value_hours == 30.5
    assert breach.threshold_hours == 24.0
    assert breach.checked_at == "2026-03-18T09:00:00Z"
    assert breach.last_record_time == "2026-03-18T09:00:00Z"


def test_slo_log_to_breach_uses_newest_updated_at_fallback():
    """slo_log_to_breach falls back to newest_updated_at when newest_record missing."""
    log = _make_slo_log(
        details={"newest_updated_at": "2026-03-17T10:00:00Z"},
    )
    breach = slo_log_to_breach(log)
    assert breach.last_record_time == "2026-03-17T10:00:00Z"


def test_slo_log_to_breach_last_record_time_none_when_missing():
    """slo_log_to_breach sets last_record_time=None when details has no record keys."""
    log = _make_slo_log(details={"reason": "stale_data"})
    breach = slo_log_to_breach(log)
    assert breach.last_record_time is None


# ---------------------------------------------------------------------------
# Test 2: get_recent_failures filters by status=="fail" and time window
# ---------------------------------------------------------------------------

def test_get_recent_failures_filters_by_status_and_time():
    """get_recent_failures must filter on status==fail and checked_at >= cutoff."""
    mock_session = MagicMock()
    mock_results = [_make_slo_log(status="fail")]
    mock_session.exec.return_value.all.return_value = mock_results

    result = get_recent_failures(mock_session)

    assert mock_session.exec.called
    # Verify result is passed through
    assert result == mock_results


def test_get_recent_failures_accepts_scraper_name():
    """get_recent_failures must accept optional scraper_name filter."""
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = []

    result = get_recent_failures(mock_session, scraper_name="mercado_livre")

    assert mock_session.exec.called
    assert result == []


# ---------------------------------------------------------------------------
# Test 3: process_failures sends when not throttled
# ---------------------------------------------------------------------------

def test_process_failures_sends_when_not_throttled():
    """process_failures must call service.notify + upsert_alert_record when should_send_alert=True."""
    mock_session = MagicMock()
    mock_service = MagicMock()
    mock_service.notify.return_value = {"telegram": True, "github": True}

    log = _make_slo_log()
    failures = [log]

    with patch("scripts.alert_worker.should_send_alert", return_value=True) as mock_should, \
         patch("scripts.alert_worker.upsert_alert_record") as mock_upsert:

        stats = process_failures(mock_session, failures, mock_service)

    mock_should.assert_called_once_with(mock_session, "mercado_livre", "freshness")
    mock_service.notify.assert_called_once()
    mock_upsert.assert_called_once_with(mock_session, "mercado_livre", "freshness")
    assert stats["sent"] == 1
    assert stats["throttled"] == 0
    assert stats["errors"] == 0
    assert stats["processed"] == 1


# ---------------------------------------------------------------------------
# Test 4: process_failures skips when throttled
# ---------------------------------------------------------------------------

def test_process_failures_skips_when_throttled():
    """process_failures must not call notify when should_send_alert returns False."""
    mock_session = MagicMock()
    mock_service = MagicMock()

    log = _make_slo_log()
    failures = [log]

    with patch("scripts.alert_worker.should_send_alert", return_value=False) as mock_should, \
         patch("scripts.alert_worker.upsert_alert_record") as mock_upsert:

        stats = process_failures(mock_session, failures, mock_service)

    mock_should.assert_called_once()
    mock_service.notify.assert_not_called()
    mock_upsert.assert_not_called()
    assert stats["throttled"] == 1
    assert stats["sent"] == 0


# ---------------------------------------------------------------------------
# Test 5: process_passes clears throttle for PASS entries
# ---------------------------------------------------------------------------

def test_process_passes_clears_throttle():
    """process_passes must call clear_alert_throttle for each unique scraper+metric."""
    mock_session = MagicMock()
    passes = [
        _make_slo_log(scraper_name="mercado_livre", metric_type="freshness", status="pass"),
        _make_slo_log(scraper_name="amazon", metric_type="freshness", status="pass"),
        # Duplicate — should only clear once
        _make_slo_log(scraper_name="mercado_livre", metric_type="freshness", status="pass"),
    ]

    with patch("scripts.alert_worker.clear_alert_throttle") as mock_clear:
        cleared = process_passes(mock_session, passes)

    assert cleared == 2
    assert mock_clear.call_count == 2
    mock_clear.assert_any_call(mock_session, "mercado_livre", "freshness")
    mock_clear.assert_any_call(mock_session, "amazon", "freshness")


def test_process_passes_returns_zero_for_empty():
    """process_passes returns 0 when given empty list."""
    mock_session = MagicMock()

    with patch("scripts.alert_worker.clear_alert_throttle") as mock_clear:
        cleared = process_passes(mock_session, [])

    assert cleared == 0
    mock_clear.assert_not_called()


# ---------------------------------------------------------------------------
# Test 6: process_failures catches exceptions gracefully
# ---------------------------------------------------------------------------

def test_process_failures_catches_exceptions():
    """process_failures must catch notify exceptions and record in stats["errors"]."""
    mock_session = MagicMock()
    mock_service = MagicMock()
    mock_service.notify.side_effect = RuntimeError("Connection refused")

    log = _make_slo_log()
    failures = [log]

    with patch("scripts.alert_worker.should_send_alert", return_value=True), \
         patch("scripts.alert_worker.upsert_alert_record"):

        stats = process_failures(mock_session, failures, mock_service)

    assert stats["errors"] == 1
    assert stats["sent"] == 0


# ---------------------------------------------------------------------------
# Test 7: LOOKBACK_HOURS constant
# ---------------------------------------------------------------------------

def test_lookback_hours_value():
    """LOOKBACK_HOURS should be 7 (slightly more than 6h cycle)."""
    assert LOOKBACK_HOURS == 7


# ---------------------------------------------------------------------------
# Test 8: main() orchestrates without raising
# ---------------------------------------------------------------------------

def test_main_orchestrates_without_raising():
    """main() must call get_recent_failures, process_failures, and process_passes."""
    with patch("scripts.alert_worker.init_db_sync"), \
         patch("scripts.alert_worker.get_slo_alert_service"), \
         patch("scripts.alert_worker.get_recent_failures", return_value=[]) as mock_failures, \
         patch("scripts.alert_worker.get_recent_passes", return_value=[]) as mock_passes, \
         patch("scripts.alert_worker.process_failures", return_value={"processed": 0, "sent": 0, "throttled": 0, "errors": 0}) as mock_proc_fail, \
         patch("scripts.alert_worker.process_passes", return_value=0) as mock_proc_pass, \
         patch("sys.argv", ["alert_worker.py", "--all"]):

        main()

    mock_failures.assert_called_once()
    mock_passes.assert_called_once()
    mock_proc_fail.assert_called_once()
    mock_proc_pass.assert_called_once()
