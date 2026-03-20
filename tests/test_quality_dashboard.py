import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.fixture
def mock_quality_rows():
    """Mock database rows for quality metrics."""
    class MockRow:
        def __init__(self, data):
            self._mapping = data
    
    return [
        MockRow({
            "scraper_name": "scraper1",
            "freshness_hours": 2.5,
            "completeness_pct": 90.0,
            "coverage_pct": 85.0,
            "product_count": 100,
            "error_rate": 0.0,
            "status": "pass",
            "checked_at": datetime(2026, 3, 20, 14, 0, 0, tzinfo=timezone.utc),
        }),
        MockRow({
            "scraper_name": "scraper2",
            "freshness_hours": 30.0,
            "completeness_pct": 50.0,
            "coverage_pct": 40.0,
            "product_count": 50,
            "error_rate": 0.5,
            "status": "fail",
            "checked_at": datetime(2026, 3, 20, 14, 0, 0, tzinfo=timezone.utc),
        }),
    ]


@pytest.fixture
def mock_empty_rows():
    """Mock empty database result."""
    return []


def test_dashboard_returns_healthy_status(mock_quality_rows):
    """Test global status is healthy when 0 scrapers fail."""
    from app.api.endpoints.quality import _classify_global_status
    
    result = _classify_global_status(0)
    assert result == "healthy"


def test_dashboard_returns_degraded_status(mock_quality_rows):
    """Test global status is degraded when 1-2 scrapers fail."""
    from app.api.endpoints.quality import _classify_global_status
    
    result = _classify_global_status(1)
    assert result == "degraded"
    
    result = _classify_global_status(2)
    assert result == "degraded"


def test_dashboard_returns_critical_status(mock_quality_rows):
    """Test global status is critical when 3+ scrapers fail."""
    from app.api.endpoints.quality import _classify_global_status
    
    result = _classify_global_status(3)
    assert result == "critical"
    
    result = _classify_global_status(10)
    assert result == "critical"


def test_dashboard_response_shape(mock_quality_rows):
    """Test dashboard returns correct JSON shape with status, scrapers, summary."""
    from app.api.endpoints.quality import quality_dashboard
    from unittest.mock import MagicMock
    
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = mock_quality_rows
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    with patch('app.api.endpoints.quality._quality_cache', {}):
        import asyncio
        result = asyncio.run(quality_dashboard(mock_session))
        
        assert "status" in result
        assert "scrapers" in result
        assert "summary" in result


def test_dashboard_scraper_object_keys(mock_quality_rows):
    """Test each scraper object has required keys."""
    from app.api.endpoints.quality import quality_dashboard
    from unittest.mock import MagicMock
    
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = mock_quality_rows
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    with patch('app.api.endpoints.quality._quality_cache', {}):
        import asyncio
        result = asyncio.run(quality_dashboard(mock_session))
        
        scraper = result["scrapers"][0]
        assert "name" in scraper
        assert "freshness_hours" in scraper
        assert "completeness_pct" in scraper
        assert "coverage_pct" in scraper
        assert "product_count" in scraper
        assert "error_rate" in scraper
        assert "status" in scraper
        assert "last_checked" in scraper


def test_dashboard_empty_db(mock_empty_rows):
    """Test response returns empty scrapers list (not error) when no data."""
    from app.api.endpoints.quality import quality_dashboard
    from unittest.mock import MagicMock
    
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = mock_empty_rows
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    with patch('app.api.endpoints.quality._quality_cache', {}):
        import asyncio
        result = asyncio.run(quality_dashboard(mock_session))
        
        assert result["scrapers"] == []
        assert result["status"] == "healthy"
        assert result["summary"]["total_scrapers"] == 0
