from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import pandas as pd


def test_detect_anomalies_improving():
    """Test detect_anomalies flags scraper as improving when metrics improve >10%."""
    from scripts.quality_report import detect_anomalies
    
    df = pd.DataFrame([
        {"scraper_name": "scraper1", "week": 10, "freshness_hours": 20.0, "completeness_pct": 60.0, "coverage_pct": 50.0, "product_count": 100, "error_rate": 0.2},
        {"scraper_name": "scraper1", "week": 11, "freshness_hours": 10.0, "completeness_pct": 75.0, "coverage_pct": 60.0, "product_count": 120, "error_rate": 0.1},
    ])
    
    result = detect_anomalies(df)
    
    assert "improving" in result
    assert "degrading" in result
    assert "scraper1" in result["improving"]


def test_detect_anomalies_degrading():
    """Test detect_anomalies flags scraper as degrading when completeness_pct drops >10%."""
    from scripts.quality_report import detect_anomalies
    
    df = pd.DataFrame([
        {"scraper_name": "scraper1", "week": 10, "freshness_hours": 10.0, "completeness_pct": 80.0, "coverage_pct": 70.0, "product_count": 100, "error_rate": 0.1},
        {"scraper_name": "scraper1", "week": 11, "freshness_hours": 20.0, "completeness_pct": 50.0, "coverage_pct": 40.0, "product_count": 80, "error_rate": 0.3},
    ])
    
    result = detect_anomalies(df)
    
    assert "scraper1" in result["degrading"]


def test_detect_anomalies_no_anomalies():
    """Test detect_anomalies returns empty lists when no anomalies exist."""
    from scripts.quality_report import detect_anomalies
    
    df = pd.DataFrame([
        {"scraper_name": "scraper1", "week": 10, "freshness_hours": 10.0, "completeness_pct": 70.0, "coverage_pct": 60.0, "product_count": 100, "error_rate": 0.1},
        {"scraper_name": "scraper1", "week": 11, "freshness_hours": 11.0, "completeness_pct": 71.0, "coverage_pct": 61.0, "product_count": 101, "error_rate": 0.11},
    ])
    
    result = detect_anomalies(df)
    
    assert result["improving"] == []
    assert result["degrading"] == []


def test_build_weekly_report_contains_table():
    """Test build_weekly_report returns HTML containing a table."""
    from scripts.quality_report import build_weekly_report
    
    df = pd.DataFrame([
        {"scraper_name": "scraper1", "week": 10, "freshness_hours": 10.0, "completeness_pct": 70.0, "coverage_pct": 60.0, "product_count": 100, "error_rate": 0.1},
        {"scraper_name": "scraper1", "week": 11, "freshness_hours": 11.0, "completeness_pct": 71.0, "coverage_pct": 61.0, "product_count": 101, "error_rate": 0.11},
    ])
    
    anomalies = {"improving": [], "degrading": []}
    reference_date = datetime.now(timezone.utc)
    
    result = build_weekly_report(df, anomalies, reference_date)
    
    assert "<table>" in result
    assert "</table>" in result


def test_build_weekly_report_contains_improving():
    """Test build_weekly_report contains Improving section when improving scrapers exist."""
    from scripts.quality_report import build_weekly_report
    
    df = pd.DataFrame([
        {"scraper_name": "scraper1", "week": 10, "freshness_hours": 20.0, "completeness_pct": 60.0, "coverage_pct": 50.0, "product_count": 100, "error_rate": 0.2},
        {"scraper_name": "scraper1", "week": 11, "freshness_hours": 10.0, "completeness_pct": 80.0, "coverage_pct": 70.0, "product_count": 120, "error_rate": 0.05},
    ])
    
    anomalies = {"improving": ["scraper1"], "degrading": []}
    reference_date = datetime.now(timezone.utc)
    
    result = build_weekly_report(df, anomalies, reference_date)
    
    assert "Improving" in result or "improving" in result.lower()
    assert "scraper1" in result


def test_build_weekly_report_contains_degrading():
    """Test build_weekly_report contains Degrading section with red styling."""
    from scripts.quality_report import build_weekly_report
    
    df = pd.DataFrame([
        {"scraper_name": "scraper1", "week": 10, "freshness_hours": 10.0, "completeness_pct": 80.0, "coverage_pct": 70.0, "product_count": 100, "error_rate": 0.1},
        {"scraper_name": "scraper1", "week": 11, "freshness_hours": 25.0, "completeness_pct": 50.0, "coverage_pct": 40.0, "product_count": 80, "error_rate": 0.4},
    ])
    
    anomalies = {"improving": [], "degrading": ["scraper1"]}
    reference_date = datetime.now(timezone.utc)
    
    result = build_weekly_report(df, anomalies, reference_date)
    
    assert "Degrading" in result or "degrading" in result.lower()
    assert "scraper1" in result
    assert "#fee2e2" in result or "fee2e2" in result


def test_send_report_with_mocked_smtp():
    """Test send_report calls smtplib.SMTP and sends EmailMessage."""
    from scripts.quality_report import send_report
    
    html = "<html><body>Test</body></html>"
    subject = "Test Report"
    
    with patch.dict("os.environ", {
        "EMAIL_HOST": "smtp.test.com",
        "EMAIL_PORT": "587",
        "EMAIL_USER": "test@test.com",
        "EMAIL_PASSWORD": "password",
        "ADMIN_EMAIL_GROUP": "admin@test.com"
    }):
        with patch("scripts.quality_report.smtplib.SMTP") as mock_smtp:
            mock_smtp_instance = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
            
            result = send_report(html, subject)
            
            assert result is True
            mock_smtp_instance.starttls.assert_called_once()
            mock_smtp_instance.login.assert_called_once()
            mock_smtp_instance.send_message.assert_called_once()


def test_send_report_returns_false_when_no_config():
    """Test send_report returns False when EMAIL_HOST is empty."""
    from scripts.quality_report import send_report
    
    html = "<html><body>Test</body></html>"
    subject = "Test Report"
    
    with patch.dict("os.environ", {
        "EMAIL_HOST": "",
        "EMAIL_USER": "",
        "ADMIN_EMAIL_GROUP": ""
    }):
        result = send_report(html, subject)
        
        assert result is False


def test_fetch_weekly_data_empty():
    """Test fetch_weekly_data returns empty DataFrame when no data."""
    from scripts.quality_report import fetch_weekly_data
    
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = []
    
    reference_date = datetime.now(timezone.utc)
    result = fetch_weekly_data(mock_session, reference_date)
    
    assert result.empty
