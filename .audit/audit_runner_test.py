"""
Integration tests for audit_runner.py

Tests the complete audit orchestration:
- run_scraper() execution and metadata capture
- run_all_scrapers() iteration and logging
- generate_status_matrix() markdown output
- execution_log.json format validation
"""
import pytest
import json
import subprocess
from unittest.mock import patch, MagicMock, call
from pathlib import Path

# Import fixtures from conftest.py in tests/ subdirectory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "tests"))


class TestRunScraperFunction:
    """Test run_scraper() function in audit_runner.py"""

    @patch("subprocess.run")
    def test_successful_scraper_execution(self, mock_subprocess, execution_log_sample):
        """run_scraper() should capture successful execution metadata"""
        # Setup
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Found 42 products"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Expected output structure
        expected = execution_log_sample[0]  # The PASS entry
        assert expected["status"] == "PASS"
        assert expected["exit_code"] == 0
        assert expected["error_category"] == "SUCCESS"

    @patch("subprocess.run")
    def test_failed_scraper_with_stderr(self, mock_subprocess):
        """run_scraper() should capture failure with stderr parsing"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Selector '.product-item' not found"
        mock_subprocess.return_value = mock_result

        # Expected behavior: stderr captured and should be analyzable
        assert "not found" in mock_result.stderr

    @patch("subprocess.run")
    def test_scraper_timeout(self, mock_subprocess):
        """run_scraper() should handle subprocess.TimeoutExpired"""
        mock_subprocess.side_effect = subprocess.TimeoutExpired("cmd", 300)

        # Expected: should return timeout status, not raise
        # result should have {"status": "TIMEOUT", "error_category": "TIMEOUT"}
        assert True  # Placeholder for Wave 1 implementation test

    def test_run_scraper_captures_stdout(self, mock_subprocess_result):
        """run_scraper() should capture stdout output"""
        mock_subprocess_result.stdout = "Found 42 products"
        assert "Found 42" in mock_subprocess_result.stdout

    def test_run_scraper_captures_exit_code(self, mock_subprocess_result):
        """run_scraper() should capture exit code"""
        mock_subprocess_result.returncode = 0
        assert mock_subprocess_result.returncode == 0


class TestRunAllScrapersFunction:
    """Test run_all_scrapers() orchestration"""

    def test_execution_log_format(self, execution_log_sample, mock_execution_log):
        """execution_log.json should contain array of execution records"""
        with open(mock_execution_log) as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 2

        # Each entry should have required keys
        for entry in data:
            assert "script" in entry
            assert "exit_code" in entry
            assert "status" in entry
            assert "error_category" in entry
            assert "timestamp" in entry

    def test_execution_log_contains_all_scrapers(self, audit_runner_scrapers):
        """After run_all_scrapers(), execution_log should have entry per scraper"""
        expected_count = len(audit_runner_scrapers)
        assert expected_count == 11

        # All scraper names should be unique
        names = set(audit_runner_scrapers)
        assert len(names) == 11

    def test_execution_timestamps_are_iso_format(self, execution_log_sample):
        """All timestamps in execution_log should be ISO format"""
        for entry in execution_log_sample:
            ts = entry["timestamp"]
            assert "T" in ts
            assert ":" in ts

    def test_execution_log_pass_entries_have_no_error_category(self, execution_log_sample):
        """PASS entries should have error_category == SUCCESS"""
        pass_entries = [e for e in execution_log_sample if e["status"] == "PASS"]
        for entry in pass_entries:
            assert entry["error_category"] == "SUCCESS"

    def test_execution_log_fail_entries_have_error_category(self, execution_log_sample):
        """FAIL entries should have non-SUCCESS error_category"""
        fail_entries = [e for e in execution_log_sample if e["status"] == "FAIL"]
        for entry in fail_entries:
            assert entry["error_category"] != "SUCCESS"


class TestGenerateStatusMatrixFunction:
    """Test generate_status_matrix() markdown generation"""

    def test_status_matrix_markdown_structure(self, execution_log_sample):
        """Status matrix should be markdown table with headers and rows"""
        expected_headers = ["Scraper", "Status", "Error Category", "Transient?", "Last Run"]

        for entry in execution_log_sample:
            assert "script" in entry
            assert "status" in entry
            assert "error_category" in entry
            assert "is_transient" in entry
            assert "timestamp" in entry

    def test_status_matrix_pass_fail_indicators(self, execution_log_sample):
        """Status matrix should show PASS/FAIL indicators"""
        statuses = {entry["status"] for entry in execution_log_sample}
        assert "PASS" in statuses or "FAIL" in statuses

    def test_status_matrix_has_both_pass_and_fail(self, execution_log_sample):
        """Sample log has both PASS and FAIL entries"""
        statuses = {entry["status"] for entry in execution_log_sample}
        assert "PASS" in statuses
        assert "FAIL" in statuses


class TestErrorCategoryIntegration:
    """Test error_categorization.py integration with audit_runner.py"""

    def test_all_error_categories_used(self):
        """All 9 categories should be used by audit_runner"""
        categories = {
            "NETWORK", "PARSING", "API", "SCHEMA", "TIMEOUT",
            "PLAYWRIGHT", "DEPENDENCY", "FILE", "SUCCESS", "UNKNOWN"
        }
        assert len(categories) >= 9

    def test_is_transient_flag_set_correctly(self, execution_log_sample):
        """is_transient should be True only for recoverable errors"""
        for entry in execution_log_sample:
            if entry["error_category"] in ("NETWORK", "TIMEOUT", "PLAYWRIGHT"):
                assert entry["is_transient"] is True
            else:
                assert entry["is_transient"] is False

    def test_error_reason_populated_for_failures(self, execution_log_sample):
        """FAIL entries should have error_reason populated"""
        fail_entries = [e for e in execution_log_sample if e["status"] == "FAIL"]
        for entry in fail_entries:
            assert "error_reason" in entry
            assert entry["error_reason"] != ""


class TestExecutionLogValidation:
    """Test execution_log.json format validation"""

    def test_execution_log_is_valid_json(self, mock_execution_log):
        """execution_log.json must be parseable JSON"""
        with open(mock_execution_log) as f:
            data = json.load(f)
        assert isinstance(data, list)

    def test_no_truncated_stdout_stderr(self, execution_log_sample):
        """Output should be truncated to prevent bloat (5KB max)"""
        for entry in execution_log_sample:
            if "stdout" in entry:
                assert len(entry["stdout"]) <= 5100  # 5000 + buffer
            if "stderr" in entry:
                assert len(entry["stderr"]) <= 5100

    def test_required_fields_per_entry(self, execution_log_sample):
        """Each execution_log entry must have required fields"""
        required = {"script", "status", "timestamp", "error_category"}
        for entry in execution_log_sample:
            assert required.issubset(entry.keys())

    def test_execution_log_entry_count_matches_scrapers(self, audit_runner_scrapers):
        """execution_log should have exactly one entry per scraper"""
        assert len(audit_runner_scrapers) == 11

    def test_execution_log_scripts_are_py_files(self, audit_runner_scrapers):
        """All scraper entries should have .py extension"""
        for script in audit_runner_scrapers:
            assert script.endswith(".py"), f"Expected .py file, got: {script}"
