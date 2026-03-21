import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


@pytest.fixture
def mock_session():
    session = MagicMock()
    return session


def test_compute_metrics_returns_dict_shape(mock_session):
    """Test compute_metrics returns dict with all required keys."""
    with patch('scripts.quality_aggregator._hours_ago') as mock_hours:
        mock_hours.return_value = datetime.now(timezone.utc)
        
        with patch('scripts.quality_aggregator.select') as mock_select:
            mock_query = MagicMock()
            mock_select.return_value = mock_query
            
            mock_session.exec.return_value.one.return_value = datetime.now(timezone.utc)
            mock_session.exec.return_value.all.return_value = []
            
            from scripts.quality_aggregator import compute_metrics
            result = compute_metrics("test_scraper", mock_session)

            assert "freshness_hours" in result
            assert "completeness_pct" in result
            assert "coverage_pct" in result
            assert "product_count" in result
            assert "error_rate" in result
            assert "status" in result


def test_persist_metrics_inserts_row(mock_session):
    """Test persist_metrics calls session.add and session.commit."""
    from scripts.quality_aggregator import persist_metrics

    metrics = {
        "freshness_hours": 1.0,
        "completeness_pct": 90.0,
        "coverage_pct": 85.0,
        "product_count": 100,
        "error_rate": 0.0,
        "status": "pass"
    }

    persist_metrics("test_scraper", "run123", metrics, mock_session)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_consolidate_queries_by_run_id(mock_session):
    """Test consolidate queries by run_id and returns summary dict."""
    from scripts.quality_aggregator import consolidate

    mock_metric1 = MagicMock()
    mock_metric1.scraper_name = "scraper1"
    mock_metric1.freshness_hours = 1.0
    mock_metric1.completeness_pct = 90.0
    mock_metric1.coverage_pct = 85.0
    mock_metric1.product_count = 100
    mock_metric1.error_rate = 0.0
    mock_metric1.status = "pass"

    mock_metric2 = MagicMock()
    mock_metric2.scraper_name = "scraper2"
    mock_metric2.freshness_hours = 30.0
    mock_metric2.completeness_pct = 50.0
    mock_metric2.coverage_pct = 40.0
    mock_metric2.product_count = 50
    mock_metric2.error_rate = 0.5
    mock_metric2.status = "fail"

    mock_session.exec.return_value.all.return_value = [mock_metric1, mock_metric2]

    result = consolidate("run123", mock_session)

    assert result["total"] == 2
    assert result["passing"] == 1
    assert result["failing"] == 1
    assert "scraper1" in result["scrapers"]
    assert "scraper2" in result["scrapers"]


def test_compute_metrics_no_offers(mock_session):
    """Test compute_metrics handles no offers gracefully."""
    with patch('scripts.quality_aggregator._hours_ago') as mock_hours:
        mock_hours.return_value = datetime.now(timezone.utc)
        
        with patch('scripts.quality_aggregator.select') as mock_select:
            mock_query = MagicMock()
            mock_select.return_value = mock_query
            
            mock_session.exec.return_value.one.return_value = None
            mock_session.exec.return_value.all.return_value = []
            
            from scripts.quality_aggregator import compute_metrics
            result = compute_metrics("test_scraper", mock_session)

            assert result["product_count"] == 0
            assert result["freshness_hours"] == float("inf")
