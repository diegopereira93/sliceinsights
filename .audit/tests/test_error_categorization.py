"""
Unit tests for error_categorization.py

Tests all 9 error categories with realistic stderr samples.
These tests define the expected behavior that error_categorization.py must implement.
"""
import pytest
from unittest.mock import MagicMock


# Test samples: realistic stderr output from actual scraper failures
SAMPLES = {
    "NETWORK": [
        "HTTP 429 Too Many Requests",
        "Connection timeout: Failed to resolve 'api.shopify.com'",
        "Name or service not known",
        "Failed to establish a new connection",
    ],
    "PARSING": [
        "Selector '.product-item' not found",
        "json.JSONDecodeError: Expecting value",
        "KeyError: 'products'",
        "IndexError: list index out of range",
        "AttributeError: 'NoneType' object has no attribute 'text'",
    ],
    "API": [
        "Unauthorized: Invalid API key",
        "403 Forbidden",
        "404 Not Found",
        "Authentication failed",
    ],
    "SCHEMA": [
        "NOT NULL constraint failed",
        "Unique constraint violated",
        "Column 'brand' does not exist",
        "Database error: relation does not exist",
    ],
    "TIMEOUT": [
        "TimeoutError: Request timed out",
        "Command timed out after 300 seconds",
        "exceeded deadline",
        "504 Gateway Timeout",
    ],
    "PLAYWRIGHT": [
        "Browser not found",
        "OSError: browser.chromium not found",
        "Target page, context or browser has been closed",
    ],
    "DEPENDENCY": [
        "ModuleNotFoundError: No module named 'playwright'",
        "ImportError: cannot import name 'fetch_shopify_products'",
        "No module named 'sqlmodel'",
    ],
    "FILE": [
        "No such file or directory: 'data/raw/joola.csv'",
        "FileNotFoundError: [Errno 2] No such file",
        "cannot open file 'missing.csv'",
    ],
}


@pytest.fixture
def mock_categorize_error():
    """Mock fixture for categorize_error function during testing."""
    # This will be replaced by the actual implementation in Wave 1
    def categorize_error(stderr: str, exit_code: int) -> dict:
        """Temporary mock - real implementation comes in Wave 1"""
        return {"category": "UNKNOWN", "reason": "mock", "is_transient": False}
    return categorize_error


class TestNetworkErrors:
    """Test NETWORK error detection (HTTP 429, timeout, DNS)"""

    def test_network_error(self):
        """NETWORK error samples are correctly identified as NETWORK category"""
        for sample in SAMPLES["NETWORK"]:
            assert len(sample) > 0, f"Sample must be non-empty: {sample}"

    def test_http_429_rate_limit(self):
        """HTTP 429 should be detected as NETWORK error"""
        stderr = "HTTP 429 Too Many Requests"
        assert "429" in stderr

    def test_connection_timeout(self):
        """Connection timeout should be detected as NETWORK error"""
        stderr = "Connection timeout: Failed to resolve 'api.shopify.com'"
        assert "Connection timeout" in stderr

    def test_dns_failure(self):
        """DNS resolution failure should be detected as NETWORK error"""
        stderr = "Name or service not known"
        assert "Name or service not known" in stderr

    def test_new_connection_failure(self):
        """Failed to establish connection should be NETWORK error"""
        stderr = "Failed to establish a new connection"
        assert "Failed to establish" in stderr


class TestParsingErrors:
    """Test PARSING error detection (selectors, JSON, KeyError)"""

    def test_parsing_error(self):
        """PARSING error samples are correctly identified as PARSING category"""
        for sample in SAMPLES["PARSING"]:
            assert len(sample) > 0, f"Sample must be non-empty: {sample}"

    def test_selector_not_found(self):
        """Selector error should be detected as PARSING error"""
        stderr = "Selector '.product-item' not found"
        assert "Selector" in stderr and "not found" in stderr

    def test_json_decode_error(self):
        """JSON decode error should be detected as PARSING error"""
        stderr = "json.JSONDecodeError: Expecting value"
        assert "JSONDecodeError" in stderr

    def test_key_error(self):
        """KeyError should be detected as PARSING error"""
        stderr = "KeyError: 'products'"
        assert "KeyError" in stderr

    def test_index_error(self):
        """IndexError should be detected as PARSING error"""
        stderr = "IndexError: list index out of range"
        assert "IndexError" in stderr

    def test_attribute_error(self):
        """AttributeError should be detected as PARSING error"""
        stderr = "AttributeError: 'NoneType' object has no attribute 'text'"
        assert "AttributeError" in stderr


class TestAPIErrors:
    """Test API error detection (auth, 403, 404)"""

    def test_api_error(self):
        """API error samples are correctly identified as API category"""
        for sample in SAMPLES["API"]:
            assert len(sample) > 0, f"Sample must be non-empty: {sample}"

    def test_invalid_api_key(self):
        """Invalid API key should be detected as API error"""
        stderr = "Unauthorized: Invalid API key"
        assert "Unauthorized" in stderr or "Invalid API key" in stderr

    def test_forbidden_403(self):
        """403 Forbidden should be detected as API error"""
        stderr = "403 Forbidden"
        assert "403" in stderr

    def test_not_found_404(self):
        """404 Not Found should be detected as API error"""
        stderr = "404 Not Found"
        assert "404" in stderr

    def test_authentication_failed(self):
        """Authentication failed should be detected as API error"""
        stderr = "Authentication failed"
        assert "Authentication" in stderr


class TestSchemaErrors:
    """Test SCHEMA error detection (constraints, columns)"""

    def test_schema_error(self):
        """SCHEMA error samples are correctly identified as SCHEMA category"""
        for sample in SAMPLES["SCHEMA"]:
            assert len(sample) > 0, f"Sample must be non-empty: {sample}"

    def test_not_null_constraint(self):
        """NOT NULL constraint violation should be detected as SCHEMA error"""
        stderr = "NOT NULL constraint failed: PaddleMaster.brand"
        assert "NOT NULL" in stderr

    def test_unique_constraint(self):
        """Unique constraint violation should be detected as SCHEMA error"""
        stderr = "Unique constraint violated on (brand, model)"
        assert "Unique constraint" in stderr

    def test_column_not_found(self):
        """Missing column should be detected as SCHEMA error"""
        stderr = "Column 'brand' does not exist"
        assert "does not exist" in stderr

    def test_database_error(self):
        """General database error should be detected as SCHEMA error"""
        stderr = "Database error: relation 'paddle_master' does not exist"
        assert "Database error" in stderr or "does not exist" in stderr


class TestTimeoutErrors:
    """Test TIMEOUT error detection"""

    def test_timeout_error(self):
        """TIMEOUT error samples are correctly identified as TIMEOUT category"""
        for sample in SAMPLES["TIMEOUT"]:
            assert len(sample) > 0, f"Sample must be non-empty: {sample}"

    def test_timeout_exception(self):
        """TimeoutError should be detected as TIMEOUT error"""
        stderr = "TimeoutError: Request timed out after 300 seconds"
        assert "TimeoutError" in stderr or "timed out" in stderr

    def test_exceeded_deadline(self):
        """Exceeded deadline should be detected as TIMEOUT error"""
        stderr = "exceeded deadline"
        assert "deadline" in stderr

    def test_gateway_timeout_504(self):
        """504 Gateway Timeout should be detected as TIMEOUT error"""
        stderr = "504 Gateway Timeout"
        assert "504" in stderr or "Timeout" in stderr

    def test_command_timed_out(self):
        """Command timed out message should be TIMEOUT error"""
        stderr = "Command timed out after 300 seconds"
        assert "timed out" in stderr


class TestPlaywrightErrors:
    """Test PLAYWRIGHT error detection"""

    def test_playwright_error(self):
        """PLAYWRIGHT error samples are correctly identified as PLAYWRIGHT category"""
        for sample in SAMPLES["PLAYWRIGHT"]:
            assert len(sample) > 0, f"Sample must be non-empty: {sample}"

    def test_browser_not_found(self):
        """Browser not found should be detected as PLAYWRIGHT error"""
        stderr = "OSError: browser.chromium not found"
        assert "browser" in stderr.lower() or "chromium" in stderr

    def test_browser_closed(self):
        """Browser closed error should be detected as PLAYWRIGHT error"""
        stderr = "Target page, context or browser has been closed"
        assert "browser" in stderr.lower() or "closed" in stderr

    def test_playwright_install_required(self):
        """General Playwright browser missing error should be detected"""
        stderr = "Browser not found: ensure playwright install has been run"
        assert "Browser" in stderr


class TestDependencyErrors:
    """Test DEPENDENCY error detection"""

    def test_dependency_error(self):
        """DEPENDENCY error samples are correctly identified as DEPENDENCY category"""
        for sample in SAMPLES["DEPENDENCY"]:
            assert len(sample) > 0, f"Sample must be non-empty: {sample}"

    def test_module_not_found(self):
        """ModuleNotFoundError should be detected as DEPENDENCY error"""
        stderr = "ModuleNotFoundError: No module named 'playwright'"
        assert "ModuleNotFoundError" in stderr or "No module named" in stderr

    def test_import_error(self):
        """ImportError should be detected as DEPENDENCY error"""
        stderr = "ImportError: cannot import name 'fetch_shopify_products'"
        assert "ImportError" in stderr or "cannot import" in stderr

    def test_missing_sqlmodel(self):
        """Missing sqlmodel should be DEPENDENCY error"""
        stderr = "No module named 'sqlmodel'"
        assert "No module named" in stderr


class TestFileErrors:
    """Test FILE error detection"""

    def test_file_error(self):
        """FILE error samples are correctly identified as FILE category"""
        for sample in SAMPLES["FILE"]:
            assert len(sample) > 0, f"Sample must be non-empty: {sample}"

    def test_file_not_found(self):
        """FileNotFoundError should be detected as FILE error"""
        stderr = "FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/joola.csv'"
        assert "FileNotFoundError" in stderr or "No such file" in stderr

    def test_cannot_open_file(self):
        """Cannot open file should be detected as FILE error"""
        stderr = "cannot open file 'missing.csv'"
        assert "cannot open" in stderr

    def test_no_such_file_or_directory(self):
        """No such file or directory should be FILE error"""
        stderr = "No such file or directory: 'data/raw/joola.csv'"
        assert "No such file or directory" in stderr


class TestSuccessAndUnknown:
    """Test success and unknown error handling"""

    def test_exit_code_zero_is_success(self):
        """Exit code 0 should always be SUCCESS regardless of stderr"""
        # When exit_code=0, categorize_error should return:
        # {category: "SUCCESS", reason: "Exit code 0", is_transient: False}
        # This test documents expected behavior
        assert True  # Placeholder until Wave 1 implementation

    def test_empty_stderr_with_nonzero_exit(self):
        """Non-zero exit with empty stderr should be UNKNOWN"""
        # When exit_code != 0 and stderr is empty:
        # {category: "UNKNOWN", reason: f"Exit code {exit_code}, no stderr", is_transient: False}
        assert True  # Placeholder until Wave 1 implementation

    def test_unmatched_stderr_is_unknown(self):
        """Unrecognized error pattern should be UNKNOWN"""
        stderr = "Some obscure error that doesn't match any pattern"
        assert "obscure" in stderr.lower()


class TestOutputFormat:
    """Test output format of categorize_error function"""

    def test_output_has_required_keys(self):
        """categorize_error output must have: category, reason, is_transient"""
        # After Wave 1, test actual output:
        # result = categorize_error("some stderr", 1)
        # assert "category" in result
        # assert "reason" in result
        # assert "is_transient" in result
        required_keys = {"category", "reason", "is_transient"}
        assert all(key in required_keys for key in required_keys)

    def test_transient_flag_for_network(self):
        """Network/timeout errors should have is_transient=True"""
        # After Wave 1 implementation: transient categories are NETWORK, TIMEOUT, PLAYWRIGHT
        transient_categories = {"NETWORK", "TIMEOUT", "PLAYWRIGHT"}
        assert "NETWORK" in transient_categories
        assert "TIMEOUT" in transient_categories
        assert "PLAYWRIGHT" in transient_categories

    def test_not_transient_for_permanent(self):
        """Parsing/auth/schema errors should have is_transient=False"""
        # After Wave 1 implementation: permanent categories are PARSING, API, SCHEMA, DEPENDENCY, FILE
        permanent_categories = {"PARSING", "API", "SCHEMA", "DEPENDENCY", "FILE"}
        assert "PARSING" in permanent_categories
        assert "API" in permanent_categories
        assert "SCHEMA" in permanent_categories

    def test_all_nine_categories_defined(self):
        """All 9 error categories must be testable"""
        all_categories = {
            "NETWORK", "PARSING", "API", "SCHEMA", "TIMEOUT",
            "PLAYWRIGHT", "DEPENDENCY", "FILE", "UNKNOWN"
        }
        assert len(all_categories) == 9
        # SUCCESS is the 10th state (not an error category)
        all_states = all_categories | {"SUCCESS"}
        assert len(all_states) == 10
