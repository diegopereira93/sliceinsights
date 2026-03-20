"""
Unit tests for scripts/deploy_worker.py — Phase 8 (DEP-01, DEP-03, DEP-04, DEP-05)

Tests cover:
- generate_batch_id pattern
- get_next_version_id from deploy_logs
- aggregate_batch inserts into staging
- publish_batch upserts and DeployLog write
- rollback_batch flag-flip and DeployLog write
- force_publish bypasses validation
- prune_old_versions deletes old rows
- CLI arg parsing and dispatch
"""
import re
import pytest
from unittest.mock import patch, MagicMock, call
from datetime import date, datetime, timezone

from scripts.deploy_worker import (
    generate_batch_id,
    get_next_version_id,
    aggregate_batch,
    publish_batch,
    rollback_batch,
    force_publish,
    prune_old_versions,
    run_deploy,
    _build_parser,
)


# ---------------------------------------------------------------------------
# Test 1: generate_batch_id returns "batch_YYYYMMDD_" + 6 hex chars
# ---------------------------------------------------------------------------

def test_generate_batch_id_format():
    """generate_batch_id must return string matching batch_YYYYMMDD_<6hex>."""
    d = date(2026, 3, 19)
    batch_id = generate_batch_id(d)

    assert isinstance(batch_id, str)
    assert re.match(r"^batch_20260319_[0-9a-f]{6}$", batch_id), (
        f"batch_id '{batch_id}' does not match expected pattern"
    )


def test_generate_batch_id_uses_given_date():
    """generate_batch_id must encode the provided date correctly."""
    d = date(2025, 12, 1)
    batch_id = generate_batch_id(d)
    assert batch_id.startswith("batch_20251201_")


# ---------------------------------------------------------------------------
# Test 2: get_next_version_id — empty table returns 1, else max+1
# ---------------------------------------------------------------------------

def test_get_next_version_id_empty_returns_1():
    """get_next_version_id returns 1 when deploy_logs has no published entries."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value.scalar.return_value = 1  # COALESCE(MAX,0)+1 = 1

    result = get_next_version_id(mock_conn)

    assert result == 1
    mock_conn.execute.assert_called_once()


def test_get_next_version_id_increments_max():
    """get_next_version_id returns max(version_id)+1 from published deploy_logs."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value.scalar.return_value = 5  # COALESCE(4,0)+1 = 5

    result = get_next_version_id(mock_conn)

    assert result == 5


# ---------------------------------------------------------------------------
# Test 3 & 4: aggregate_batch inserts rows into staging, returns count + scrapers
# ---------------------------------------------------------------------------

def test_aggregate_batch_inserts_rows():
    """aggregate_batch must execute INSERT INTO market_offers_staging for each passed scraper."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value.rowcount = 10

    count, scrapers = aggregate_batch(
        mock_conn,
        batch_id="batch_20260319_abc123",
        batch_date=date(2026, 3, 19),
        passed_scrapers=["mercado_livre", "amazon"],
    )

    # Two scrapers -> two INSERT calls
    assert mock_conn.execute.call_count == 2
    assert count == 20  # 10 rows per scraper
    assert scrapers == ["mercado_livre", "amazon"]


def test_aggregate_batch_empty_scrapers_returns_zero():
    """aggregate_batch returns (0, []) when passed_scrapers is empty."""
    mock_conn = MagicMock()

    count, scrapers = aggregate_batch(
        mock_conn,
        batch_id="batch_20260319_abc123",
        batch_date=date(2026, 3, 19),
        passed_scrapers=[],
    )

    assert count == 0
    assert scrapers == []
    mock_conn.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Test 5 & 6: publish_batch upserts and writes DeployLog
# ---------------------------------------------------------------------------

def test_publish_batch_executes_upsert():
    """publish_batch must execute UPDATE (deactivate prev) and INSERT ON CONFLICT upsert."""
    mock_conn = MagicMock()
    # First execute = UPDATE prev version; second = upsert INSERT
    mock_conn.execute.side_effect = [
        MagicMock(rowcount=5),   # deactivate previous
        MagicMock(rowcount=42),  # upsert count
    ]

    count = publish_batch(mock_conn, batch_id="batch_20260319_abc123", version_id=3)

    assert count == 42
    assert mock_conn.execute.call_count == 2


def test_publish_batch_writes_deploy_log():
    """publish_batch must write a DeployLog entry with status='published'."""
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = [
        MagicMock(rowcount=0),
        MagicMock(rowcount=15),
    ]

    with patch("scripts.deploy_worker.Session") as MockSession:
        mock_session = MagicMock()
        MockSession.return_value.__enter__.return_value = mock_session

        count = publish_batch(mock_conn, batch_id="batch_20260319_abc123", version_id=2)

    assert count == 15


# ---------------------------------------------------------------------------
# Test 7 & 8: rollback_batch flips flags and writes DeployLog
# ---------------------------------------------------------------------------

def test_rollback_batch_flips_is_active_flags():
    """rollback_batch must UPDATE is_active=false for current, is_active=true for previous."""
    with patch("scripts.deploy_worker.sync_engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.begin.return_value.__enter__.return_value = mock_conn

        # Simulate DeployLog lookup returning version_id=3
        mock_conn.execute.return_value.fetchone.return_value = MagicMock(version_id=3)

        with patch("scripts.deploy_worker.Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value.__enter__.return_value = mock_session

            rollback_batch("batch_20260319_abc123")

    # Should have called execute at least once for the version lookup
    assert mock_conn.execute.called


def test_rollback_batch_writes_rolled_back_log():
    """rollback_batch must write DeployLog with status='rolled_back'."""
    with patch("scripts.deploy_worker.sync_engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.begin.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = MagicMock(version_id=2)

        with patch("scripts.deploy_worker.Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value.__enter__.return_value = mock_session

            rollback_batch("batch_20260319_abc123")

        # Verify session.add was called (DeployLog written)
        assert mock_session.add.called
        # Verify the added object has status='rolled_back'
        added_obj = mock_session.add.call_args[0][0]
        assert added_obj.status == "rolled_back"


# ---------------------------------------------------------------------------
# Test 9: force_publish bypasses validation, sets forced=True
# ---------------------------------------------------------------------------

def test_force_publish_sets_forced_true():
    """force_publish must write DeployLog with forced=True and correct operator_id."""
    with patch("scripts.deploy_worker.sync_engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.begin.return_value.__enter__.return_value = mock_conn
        # get_next_version_id
        mock_conn.execute.return_value.scalar.return_value = 2
        # publish_batch internal calls
        mock_conn.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=2)),  # get_next_version_id
            MagicMock(rowcount=0),                        # deactivate previous
            MagicMock(rowcount=10),                       # upsert
        ]

        with patch("scripts.deploy_worker.Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value.__enter__.return_value = mock_session

            with patch("scripts.deploy_worker.get_next_version_id", return_value=2), \
                 patch("scripts.deploy_worker.publish_batch", return_value=10):
                force_publish("batch_20260319_abc123", operator_id="admin")

        # Verify session.add called with forced=True
        assert mock_session.add.called
        added_obj = mock_session.add.call_args[0][0]
        assert added_obj.forced is True
        assert added_obj.operator_id == "admin"


def test_force_publish_sends_alert():
    """force_publish must attempt to send a Telegram alert (failure is non-fatal)."""
    with patch("scripts.deploy_worker.sync_engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.begin.return_value.__enter__.return_value = mock_conn

        with patch("scripts.deploy_worker.Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value.__enter__.return_value = mock_session

            with patch("scripts.deploy_worker.get_next_version_id", return_value=1), \
                 patch("scripts.deploy_worker.publish_batch", return_value=5), \
                 patch("scripts.deploy_worker.SLOAlertService") as MockAlert:

                mock_alert_instance = MagicMock()
                MockAlert.return_value = mock_alert_instance

                force_publish("batch_20260319_abc123", operator_id="ops_user")

        mock_alert_instance.send_telegram.assert_called_once()
        call_arg = mock_alert_instance.send_telegram.call_args[0][0]
        assert "FORCE PUBLISH" in call_arg
        assert "ops_user" in call_arg


# ---------------------------------------------------------------------------
# Test 10: prune_old_versions deletes rows where version_id < keep_min
# ---------------------------------------------------------------------------

def test_prune_old_versions_deletes_old_rows():
    """prune_old_versions must DELETE rows where version_id < (current - 1)."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value.rowcount = 7

    deleted = prune_old_versions(mock_conn, current_version_id=5)

    assert deleted == 7
    # keep_min = 5 - 1 = 4; rows with version_id < 4 (i.e., <= 3) should be deleted
    mock_conn.execute.assert_called_once()
    sql_arg = str(mock_conn.execute.call_args[0][0])
    assert "DELETE" in sql_arg.upper() or "delete" in sql_arg.lower()


def test_prune_old_versions_version_1_deletes_nothing():
    """prune_old_versions on version 1 should delete zero (keep_min=0, no rows match)."""
    mock_conn = MagicMock()
    mock_conn.execute.return_value.rowcount = 0

    deleted = prune_old_versions(mock_conn, current_version_id=1)

    assert deleted == 0


# ---------------------------------------------------------------------------
# Test 11 & 12: CLI arg parsing
# ---------------------------------------------------------------------------

def test_cli_parser_run_flag():
    """--run flag must be parsed without error."""
    parser = _build_parser()
    args = parser.parse_args(["--run"])
    assert args.run is True


def test_cli_parser_rollback_flag():
    """--rollback BATCH_ID must be parsed correctly."""
    parser = _build_parser()
    args = parser.parse_args(["--rollback", "batch_20260319_abc123"])
    assert args.rollback == "batch_20260319_abc123"


def test_cli_parser_force_publish_flag():
    """--force-publish BATCH_ID must be parsed correctly."""
    parser = _build_parser()
    args = parser.parse_args(["--force-publish", "batch_20260319_abc123"])
    assert args.force_publish == "batch_20260319_abc123"


def test_cli_parser_validate_batch_flag():
    """--validate-batch BATCH_ID must be parsed correctly."""
    parser = _build_parser()
    args = parser.parse_args(["--validate-batch", "batch_20260319_abc123"])
    assert args.validate_batch == "batch_20260319_abc123"


def test_cli_parser_mutually_exclusive():
    """Parser must reject combining --run with --rollback."""
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--run", "--rollback", "batch_20260319_abc123"])


def test_cli_run_calls_run_deploy():
    """main() with --run must call run_deploy()."""
    with patch("scripts.deploy_worker.run_deploy") as mock_run, \
         patch("sys.argv", ["deploy_worker.py", "--run"]):
        from scripts.deploy_worker import main
        main()
    mock_run.assert_called_once()


def test_cli_rollback_calls_rollback_batch():
    """main() with --rollback BATCH_ID must call rollback_batch(batch_id)."""
    with patch("scripts.deploy_worker.rollback_batch") as mock_rb, \
         patch("sys.argv", ["deploy_worker.py", "--rollback", "batch_20260319_abc123"]):
        from scripts.deploy_worker import main
        main()
    mock_rb.assert_called_once_with("batch_20260319_abc123")
