"""
Unit tests for scripts/slo_validator.py — SLO validation script.

Coverage:
- Test 1: check_freshness returns status="pass" when age_hours < 24
- Test 2: check_freshness returns status="fail" when age_hours > 24
- Test 3: check_freshness returns status="skip" when no data exists
- Test 4: check_completeness returns status="pass" when 24 < age_hours < 168
- Test 5: check_completeness returns status="skip" when age_hours < 24
- Test 6: check_completeness returns status="fail" when age_hours > 168
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta


class TestCheckFreshness:
    def test_check_freshness_pass_when_within_slo(self):
        """check_freshness returns status='pass' when data is within SLO window (< 24h)."""
        from scripts.slo_validator import check_freshness

        session = MagicMock()

        now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
        two_hours_ago = now - timedelta(hours=2)

        mock_row = MagicMock()
        mock_row.store_name = "mercado_livre"
        mock_row.newest = two_hours_ago

        session.exec.return_value.all.return_value = [mock_row]

        with patch("scripts.slo_validator._now_utc", return_value=now):
            with patch("scripts.slo_validator.SLOLog") as MockSLOLog:
                mock_log = MagicMock()
                mock_log.scraper_name = "mercado_livre"
                mock_log.status = ""
                mock_log.details = {}
                MockSLOLog.return_value = mock_log
                session.add.return_value = None
                session.commit.return_value = None
                session.refresh.return_value = None

                check_freshness(session, scraper_name="mercado_livre")

                call_args = MockSLOLog.call_args
                assert call_args is not None
                kwargs = call_args.kwargs
                assert kwargs["status"] == "pass"
                assert kwargs["details"]["reason"] == "within_slo"

    def test_check_freshness_fail_when_stale(self):
        """check_freshness returns status='fail' when data is stale (> 24h)."""
        from scripts.slo_validator import check_freshness

        session = MagicMock()

        now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
        thirty_hours_ago = now - timedelta(hours=30)

        mock_row = MagicMock()
        mock_row.store_name = "mercado_livre"
        mock_row.newest = thirty_hours_ago

        session.exec.return_value.all.return_value = [mock_row]

        with patch("scripts.slo_validator._now_utc", return_value=now):
            with patch("scripts.slo_validator.SLOLog") as MockSLOLog:
                mock_log = MagicMock()
                mock_log.scraper_name = "mercado_livre"
                mock_log.status = ""
                MockSLOLog.return_value = mock_log
                session.add.return_value = None
                session.commit.return_value = None
                session.refresh.return_value = None

                check_freshness(session, scraper_name="mercado_livre")

                call_args = MockSLOLog.call_args
                assert call_args is not None
                kwargs = call_args.kwargs
                assert kwargs["status"] == "fail"
                assert kwargs["details"]["reason"] == "stale_data"

    def test_check_freshness_skip_when_no_data(self):
        """check_freshness returns status='skip' when no data exists yet."""
        from scripts.slo_validator import check_freshness

        session = MagicMock()

        session.exec.return_value.all.return_value = []

        with patch("scripts.slo_validator.SLOLog") as MockSLOLog:
            mock_log = MagicMock()
            mock_log.scraper_name = "mercado_livre"
            mock_log.status = ""
            MockSLOLog.return_value = mock_log
            session.add.return_value = None
            session.commit.return_value = None
            session.refresh.return_value = None

            check_freshness(session, scraper_name="mercado_livre")

            call_args = MockSLOLog.call_args
            assert call_args is not None
            kwargs = call_args.kwargs
            assert kwargs["status"] == "skip"
            assert kwargs["details"]["reason"] == "no_data_yet"


class TestCheckCompleteness:
    def test_check_completeness_pass_when_within_slo(self):
        """check_completeness returns status='pass' when 24h < age_hours < 168h."""
        from scripts.slo_validator import check_completeness

        session = MagicMock()

        now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
        forty_eight_hours_ago = now - timedelta(hours=48)

        session.exec.return_value.one_or_none.return_value = forty_eight_hours_ago

        with patch("scripts.slo_validator._now_utc", return_value=now):
            with patch("scripts.slo_validator.SLOLog") as MockSLOLog:
                mock_log = MagicMock()
                mock_log.scraper_name = "__all__"
                mock_log.status = ""
                MockSLOLog.return_value = mock_log
                session.add.return_value = None
                session.commit.return_value = None
                session.refresh.return_value = None

                check_completeness(session, scraper_name=None)

                call_args = MockSLOLog.call_args
                assert call_args is not None
                kwargs = call_args.kwargs
                assert kwargs["status"] == "pass"
                assert kwargs["details"]["reason"] == "within_slo"

    def test_check_completeness_skip_when_recently_updated(self):
        """check_completeness returns status='skip' when age_hours < 24h."""
        from scripts.slo_validator import check_completeness

        session = MagicMock()

        now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
        two_hours_ago = now - timedelta(hours=2)

        session.exec.return_value.one_or_none.return_value = two_hours_ago

        with patch("scripts.slo_validator._now_utc", return_value=now):
            with patch("scripts.slo_validator.SLOLog") as MockSLOLog:
                mock_log = MagicMock()
                mock_log.scraper_name = "__all__"
                mock_log.status = ""
                MockSLOLog.return_value = mock_log
                session.add.return_value = None
                session.commit.return_value = None
                session.refresh.return_value = None

                check_completeness(session, scraper_name=None)

                call_args = MockSLOLog.call_args
                assert call_args is not None
                kwargs = call_args.kwargs
                assert kwargs["status"] == "skip"
                assert kwargs["details"]["reason"] == "recently_updated"

    def test_check_completeness_fail_when_stale(self):
        """check_completeness returns status='fail' when age_hours > 168h."""
        from scripts.slo_validator import check_completeness

        session = MagicMock()

        now = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
        two_hundred_hours_ago = now - timedelta(hours=200)

        session.exec.return_value.one_or_none.return_value = two_hundred_hours_ago

        with patch("scripts.slo_validator._now_utc", return_value=now):
            with patch("scripts.slo_validator.SLOLog") as MockSLOLog:
                mock_log = MagicMock()
                mock_log.scraper_name = "__all__"
                mock_log.status = ""
                MockSLOLog.return_value = mock_log
                session.add.return_value = None
                session.commit.return_value = None
                session.refresh.return_value = None

                check_completeness(session, scraper_name=None)

                call_args = MockSLOLog.call_args
                assert call_args is not None
                kwargs = call_args.kwargs
                assert kwargs["status"] == "fail"
                assert kwargs["details"]["reason"] == "stale_data"