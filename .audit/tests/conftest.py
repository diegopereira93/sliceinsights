"""
Shared pytest fixtures for audit tests.

Provides:
- execution_log_sample: sample execution_log.json structure
- mock_execution_log: temporary execution_log.json file
- mock_subprocess_result: mocked subprocess.run() result
- audit_runner_scrapers: list of 11 scraper script names
- audit_runner_config: configuration for audit_runner.py
- setup_audit_directory: temp .audit/ directory structure
"""
import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch


@pytest.fixture
def execution_log_sample():
    """Sample execution_log.json structure (2 entries: 1 pass, 1 fail)"""
    return [
        {
            "script": "scrape_joola.py",
            "exit_code": 0,
            "stdout": "Found 42 products",
            "stderr": "",
            "timestamp": "2026-03-19T14:30:00.000000",
            "status": "PASS",
            "error_category": "SUCCESS",
            "error_reason": "Exit code 0",
            "is_transient": False,
        },
        {
            "script": "scrape_justpaddles.py",
            "exit_code": 1,
            "stdout": "Starting Playwright browser...",
            "stderr": "Selector '.product-item' not found",
            "timestamp": "2026-03-19T14:31:15.000000",
            "status": "FAIL",
            "error_category": "PARSING",
            "error_reason": "Selector '.product-item' not found",
            "is_transient": False,
        },
    ]


@pytest.fixture
def mock_execution_log(tmp_path):
    """Create a temporary execution_log.json file in a temp directory"""
    log_file = tmp_path / "execution_log.json"
    sample_data = [
        {
            "script": "scrape_joola.py",
            "exit_code": 0,
            "status": "PASS",
            "error_category": "SUCCESS",
            "error_reason": "Exit code 0",
            "is_transient": False,
            "timestamp": "2026-03-19T14:30:00.000000",
        },
        {
            "script": "scrape_shark.py",
            "exit_code": 1,
            "status": "FAIL",
            "error_category": "NETWORK",
            "error_reason": "HTTP 429",
            "is_transient": True,
            "timestamp": "2026-03-19T14:31:00.000000",
        },
    ]
    with open(log_file, "w") as f:
        json.dump(sample_data, f)
    return log_file


@pytest.fixture
def mock_subprocess_result():
    """Mock result from subprocess.run()"""
    result = MagicMock()
    result.returncode = 0
    result.stdout = "Sample output"
    result.stderr = ""
    return result


@pytest.fixture
def audit_runner_scrapers():
    """List of 11 scraper script names for audit_runner.py to execute"""
    return [
        "scrape_joola.py",
        "scrape_shark.py",
        "scrape_supremo.py",
        "scrape_yosports.py",
        "scrape_pcklhouse.py",
        "scrape_propadel.py",
        "scrape_justpaddles.py",
        "scrape_brain_paddles.py",
        "ingest_pb_studio_csv.py",
        "ingest_johnkew_csv.py",
        "fetch_johnkew.py",
    ]


@pytest.fixture
def audit_runner_config():
    """Configuration for audit_runner.py"""
    return {
        "timeout_seconds": 300,
        "log_file": ".audit/execution_log.json",
        "status_file": ".audit/status_matrix.md",
        "max_output_bytes": 5000,
    }


@pytest.fixture(scope="function")
def setup_audit_directory(tmp_path):
    """Create .audit/ directory structure for test"""
    audit_dir = tmp_path / ".audit"
    audit_dir.mkdir(exist_ok=True)
    (audit_dir / "tests").mkdir(exist_ok=True)
    return audit_dir
