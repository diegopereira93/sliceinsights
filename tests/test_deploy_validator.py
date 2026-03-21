"""
Unit tests for deploy_validator.py — pre-deploy validation script.

Coverage:
- Test 1: run_pre_deploy_validation returns (True, []) when all SLO checks pass and no corruption
- Test 2: run_pre_deploy_validation returns (False, [...]) when freshness fails for a scraper
- Test 3: run_pre_deploy_validation returns (False, [...]) when staging has NULL price_brl or url
- Test 4: run_pre_deploy_validation returns (False, [...]) with multiple failures when both fail
- Test 5: run_corruption_audit returns (True, []) for clean staging batch
- Test 6: run_corruption_audit returns (False, [...]) when record count is 0 (empty batch)
- Test 7: check_slo_gate queries slo_logs for the calendar day window and returns scraper lists
"""

from unittest.mock import patch, MagicMock
from datetime import date


# ---------------------------------------------------------------------------
# Helpers to build fake DB result rows
# ---------------------------------------------------------------------------

def _scalar_result(value):
    """Mock a scalar execute result."""
    m = MagicMock()
    m.scalar.return_value = value
    m.fetchall.return_value = [value]
    return m


def _rows_result(rows):
    """Mock a fetchall execute result returning a list of Row-like objects."""
    m = MagicMock()
    m.fetchall.return_value = rows
    return m


def _row(scraper_name):
    r = MagicMock()
    r.scraper_name = scraper_name
    return r


# ---------------------------------------------------------------------------
# Test 7: check_slo_gate — SLO gate day-window query
# ---------------------------------------------------------------------------

class TestCheckSloGate:
    def test_slo_gate_pass_returns_passing_scrapers(self):
        """check_slo_gate returns passed scrapers list and empty failed list when all pass."""
        from scripts.deploy_validator import check_slo_gate

        session = MagicMock()
        batch_date = date(2026, 3, 19)

        # First execute call: passed scrapers
        passed_result = _rows_result([_row("mercado_livre"), _row("shopee")])
        # Second execute call: failed scrapers
        failed_result = _rows_result([])

        session.execute.side_effect = [passed_result, failed_result]

        passed, failed = check_slo_gate(session, batch_date)

        assert "mercado_livre" in passed
        assert "shopee" in passed
        assert failed == []

    def test_slo_gate_fail_returns_failed_scrapers(self):
        """check_slo_gate returns failed scrapers when some have status=fail."""
        from scripts.deploy_validator import check_slo_gate

        session = MagicMock()
        batch_date = date(2026, 3, 19)

        passed_result = _rows_result([_row("shopee")])
        failed_result = _rows_result([_row("mercado_livre")])

        session.execute.side_effect = [passed_result, failed_result]

        passed, failed = check_slo_gate(session, batch_date)

        assert "shopee" in passed
        assert "mercado_livre" in failed

    def test_slo_gate_finds_freshness_pass_rows(self):
        """Deploy gate finds scrapers with status='pass' written by fixed check_freshness."""
        from scripts.deploy_validator import check_slo_gate

        session = MagicMock()
        batch_date = date(2026, 3, 20)

        passed_result = _rows_result([_row("mercado_livre"), _row("shopee"), _row("amazon")])
        failed_result = _rows_result([])

        session.execute.side_effect = [passed_result, failed_result]

        passed, failed = check_slo_gate(session, batch_date)

        assert len(passed) == 3
        assert "mercado_livre" in passed
        assert "shopee" in passed
        assert "amazon" in passed
        assert failed == []

    def test_slo_gate_mixed_pass_and_fail(self):
        """Deploy gate correctly separates passed and failed scrapers."""
        from scripts.deploy_validator import check_slo_gate

        session = MagicMock()
        batch_date = date(2026, 3, 20)

        passed_result = _rows_result([_row("shopee")])
        failed_result = _rows_result([_row("mercado_livre")])

        session.execute.side_effect = [passed_result, failed_result]

        passed, failed = check_slo_gate(session, batch_date)

        assert passed == ["shopee"]
        assert failed == ["mercado_livre"]


# ---------------------------------------------------------------------------
# Test 5 & 6: run_corruption_audit
# ---------------------------------------------------------------------------

class TestRunCorruptionAudit:
    def test_clean_batch_passes(self):
        """Test 5: run_corruption_audit returns (True, []) for clean staging batch."""
        from scripts.deploy_validator import run_corruption_audit

        session = MagicMock()

        # total rows = 100, NULL price_brl = 0, NULL url = 0, NULL store_name = 0, NULL paddle_id = 0
        session.execute.side_effect = [
            _scalar_result(100),  # total rows
            _scalar_result(0),    # NULL price_brl
            _scalar_result(0),    # NULL url
            _scalar_result(0),    # NULL store_name
            _scalar_result(0),    # NULL paddle_id
        ]

        ok, failures = run_corruption_audit(session, "batch_20260319_abc")

        assert ok is True
        assert failures == []

    def test_empty_batch_fails(self):
        """Test 6: run_corruption_audit returns (False, [...]) when record count is 0."""
        from scripts.deploy_validator import run_corruption_audit

        session = MagicMock()
        session.execute.return_value = _scalar_result(0)  # total rows = 0

        ok, failures = run_corruption_audit(session, "batch_20260319_empty")

        assert ok is False
        assert len(failures) == 1
        assert "Empty batch" in failures[0] or "empty" in failures[0].lower()

    def test_null_price_brl_fails(self):
        """Corruption: NULL price_brl rows detected."""
        from scripts.deploy_validator import run_corruption_audit

        session = MagicMock()
        session.execute.side_effect = [
            _scalar_result(50),   # total rows
            _scalar_result(3),    # 3 NULL price_brl
            _scalar_result(0),    # NULL url
            _scalar_result(0),    # NULL store_name
            _scalar_result(0),    # NULL paddle_id
        ]

        ok, failures = run_corruption_audit(session, "batch_20260319_bad")

        assert ok is False
        assert any("price_brl" in f for f in failures)

    def test_null_url_fails(self):
        """Corruption: NULL url rows detected."""
        from scripts.deploy_validator import run_corruption_audit

        session = MagicMock()
        session.execute.side_effect = [
            _scalar_result(50),   # total rows
            _scalar_result(0),    # NULL price_brl
            _scalar_result(2),    # 2 NULL url
            _scalar_result(0),    # NULL store_name
            _scalar_result(0),    # NULL paddle_id
        ]

        ok, failures = run_corruption_audit(session, "batch_20260319_bad")

        assert ok is False
        assert any("url" in f for f in failures)


# ---------------------------------------------------------------------------
# Tests 1-4: run_pre_deploy_validation
# ---------------------------------------------------------------------------

class TestRunPreDeployValidation:
    def test_all_pass_returns_true_empty_list(self):
        """Test 1: returns (True, []) when SLO gate passes and no corruption."""
        from scripts.deploy_validator import run_pre_deploy_validation

        batch_date = date(2026, 3, 19)

        with patch("scripts.deploy_validator.check_slo_gate") as mock_slo, \
             patch("scripts.deploy_validator.run_corruption_audit") as mock_audit, \
             patch("scripts.deploy_validator.Session") as mock_session_cls:

            mock_session_cls.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

            mock_slo.return_value = (["mercado_livre", "shopee"], [])
            mock_audit.return_value = (True, [])

            ok, failures = run_pre_deploy_validation("batch_20260319_abc", batch_date)

        assert ok is True
        assert failures == []

    def test_freshness_fail_returns_false_with_message(self):
        """Test 2: returns (False, [...]) when SLO freshness fails."""
        from scripts.deploy_validator import run_pre_deploy_validation

        batch_date = date(2026, 3, 19)

        with patch("scripts.deploy_validator.check_slo_gate") as mock_slo, \
             patch("scripts.deploy_validator.run_corruption_audit") as mock_audit, \
             patch("scripts.deploy_validator.Session") as mock_session_cls:

            mock_session_cls.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

            mock_slo.return_value = (["shopee"], ["mercado_livre"])
            mock_audit.return_value = (True, [])

            ok, failures = run_pre_deploy_validation("batch_20260319_abc", batch_date)

        assert ok is False
        assert len(failures) >= 1
        assert any("mercado_livre" in f or "SLO" in f for f in failures)

    def test_corruption_fail_returns_false_with_message(self):
        """Test 3: returns (False, [...]) when staging has NULL price_brl or url."""
        from scripts.deploy_validator import run_pre_deploy_validation

        batch_date = date(2026, 3, 19)

        with patch("scripts.deploy_validator.check_slo_gate") as mock_slo, \
             patch("scripts.deploy_validator.run_corruption_audit") as mock_audit, \
             patch("scripts.deploy_validator.Session") as mock_session_cls:

            mock_session_cls.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

            mock_slo.return_value = (["mercado_livre", "shopee"], [])
            mock_audit.return_value = (False, ["Corruption: 5 rows with NULL price_brl or url"])

            ok, failures = run_pre_deploy_validation("batch_20260319_abc", batch_date)

        assert ok is False
        assert any("Corruption" in f or "NULL" in f or "price_brl" in f for f in failures)

    def test_both_fail_returns_multiple_failures(self):
        """Test 4: returns (False, [...]) with multiple failures when both SLO and corruption fail."""
        from scripts.deploy_validator import run_pre_deploy_validation

        batch_date = date(2026, 3, 19)

        with patch("scripts.deploy_validator.check_slo_gate") as mock_slo, \
             patch("scripts.deploy_validator.run_corruption_audit") as mock_audit, \
             patch("scripts.deploy_validator.Session") as mock_session_cls:

            mock_session_cls.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

            mock_slo.return_value = ([], ["mercado_livre", "shopee"])
            mock_audit.return_value = (False, ["Corruption: 3 rows with NULL price_brl"])

            ok, failures = run_pre_deploy_validation("batch_20260319_bad", batch_date)

        assert ok is False
        assert len(failures) >= 2
