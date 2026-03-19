"""
Error categorization module for scraper health audit.

Classifies scraper stderr output into structured failure categories to distinguish
transient (retryable) failures from permanent (code/schema) failures.
"""
import re
from typing import Optional

# Category constants
SUCCESS = "SUCCESS"
NETWORK = "NETWORK"
PARSING = "PARSING"
API = "API"
SCHEMA = "SCHEMA"
TIMEOUT = "TIMEOUT"
PLAYWRIGHT = "PLAYWRIGHT"
DEPENDENCY = "DEPENDENCY"
FILE = "FILE"
UNKNOWN = "UNKNOWN"

# Pattern definitions: (category, [patterns], is_transient, description)
# Order matters — first match wins
_CATEGORY_PATTERNS = [
    (
        TIMEOUT,
        [
            r"TimeoutError",
            r"timed out",
            r"exceeded deadline",
            r"\b504\b",
            r"Read timed out",
            r"ConnectTimeout",
            r"requests\.exceptions\.Timeout",
        ],
        True,
        "Operation exceeded time limit",
    ),
    (
        PLAYWRIGHT,
        [
            r"Browser not found",
            r"OSError.*browser",
            r"chromium",
            r"playwright\._impl",
            r"BrowserType\.launch",
            r"Executable doesn.t exist",
            r"playwright install",
        ],
        True,
        "Playwright browser dependency issue",
    ),
    (
        NETWORK,
        [
            r"HTTP 429",
            r"429 Too Many Requests",
            r"Connection timeout",
            r"Name or service not known",
            r"Failed to resolve",
            r"ConnectionError",
            r"ConnectionRefusedError",
            r"RemoteDisconnected",
            r"Network is unreachable",
            r"requests\.exceptions\.ConnectionError",
            r"requests\.exceptions\.HTTPError",
            r"Max retries exceeded",
            r"NewConnectionError",
        ],
        True,
        "Network connectivity or rate-limiting failure",
    ),
    (
        DEPENDENCY,
        [
            r"ModuleNotFoundError",
            r"ImportError",
            r"No module named",
            r"cannot import name",
        ],
        False,
        "Missing Python module or import error",
    ),
    (
        FILE,
        [
            r"No such file or directory",
            r"FileNotFoundError",
            r"cannot open",
            r"IsADirectoryError",
            r"PermissionError",
        ],
        False,
        "File system access error",
    ),
    (
        API,
        [
            r"Unauthorized",
            r"\b403\b",
            r"\b401\b",
            r"Authentication failed",
            r"Invalid API key",
            r"API key",
            r"Access denied",
            r"\b404\b.*endpoint",
            r"endpoint not found",
        ],
        False,
        "API authentication or authorization failure",
    ),
    (
        SCHEMA,
        [
            r"NOT NULL",
            r"Unique constraint",
            r"Column does not exist",
            r"Database error",
            r"IntegrityError",
            r"psycopg2\.errors",
            r"sqlalchemy\.exc",
            r"ProgrammingError",
            r"OperationalError.*database",
            r"relation.*does not exist",
            r"column.*does not exist",
        ],
        False,
        "Database schema or integrity constraint failure",
    ),
    (
        PARSING,
        [
            r"[Ss]elector",
            r"JSON decode",
            r"JSONDecodeError",
            r"KeyError",
            r"IndexError",
            r"[Aa]ttribute[Ee]rror",
            r"AttributeError",
            r"ValueError",
            r"TypeError",
            r"NoneType",
            r"'NoneType' object",
            r"list index out of range",
            r"string indices must be integers",
            r"expected string or bytes",
        ],
        False,
        "Data parsing or extraction failure",
    ),
]

# Pre-compile all patterns once at module load
_COMPILED_PATTERNS: list[tuple[str, list[re.Pattern], bool, str]] = []
for _cat, _pats, _transient, _desc in _CATEGORY_PATTERNS:
    _compiled = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in _pats]
    _COMPILED_PATTERNS.append((_cat, _compiled, _transient, _desc))


def categorize_error(stderr: str, exit_code: int) -> dict:
    """
    Classify scraper failure from stderr output and exit code.

    Args:
        stderr: Captured stderr text from scraper execution.
        exit_code: Process exit code (0 = success).

    Returns:
        dict with keys:
            category (str): One of SUCCESS, NETWORK, PARSING, API, SCHEMA,
                            TIMEOUT, PLAYWRIGHT, DEPENDENCY, FILE, UNKNOWN
            reason (str): Human-readable explanation of the failure
            is_transient (bool): True if failure may resolve on retry
            matched_pattern (Optional[str]): The regex pattern that matched, or None
    """
    # Exit code 0 = success regardless of stderr content (warnings are ok)
    if exit_code == 0:
        return {
            "category": SUCCESS,
            "reason": "Exit code 0",
            "is_transient": False,
            "matched_pattern": None,
        }

    # Non-zero exit but no stderr to classify
    if not stderr or not stderr.strip():
        return {
            "category": UNKNOWN,
            "reason": f"Exit code {exit_code}, no stderr output",
            "is_transient": False,
            "matched_pattern": None,
        }

    # Scan stderr against all category patterns (first match wins)
    for category, compiled_patterns, is_transient, description in _COMPILED_PATTERNS:
        for pattern in compiled_patterns:
            match = pattern.search(stderr)
            if match:
                matched_text = match.group(0)
                return {
                    "category": category,
                    "reason": f"{description}: {matched_text!r}",
                    "is_transient": is_transient,
                    "matched_pattern": pattern.pattern,
                }

    # No pattern matched
    # Extract last non-empty line from stderr as reason hint
    lines = [ln.strip() for ln in stderr.splitlines() if ln.strip()]
    hint = lines[-1][:200] if lines else "No details"
    return {
        "category": UNKNOWN,
        "reason": f"Exit code {exit_code}, unrecognized error: {hint}",
        "is_transient": False,
        "matched_pattern": None,
    }


def _run_self_tests() -> None:
    """Quick smoke tests to validate categorization logic."""
    cases = [
        # (stderr, exit_code, expected_category)
        ("", 0, SUCCESS),
        ("", 1, UNKNOWN),
        ("HTTP 429 Too Many Requests", 1, NETWORK),
        ("Connection timeout after 30s", 1, NETWORK),
        ("Name or service not known", 1, NETWORK),
        ("TimeoutError: operation timed out", 1, TIMEOUT),
        ("Read timed out", 1, TIMEOUT),
        ("Browser not found at path", 1, PLAYWRIGHT),
        ("OSError: browser not installed", 1, PLAYWRIGHT),
        ("ModuleNotFoundError: No module named 'requests'", 1, DEPENDENCY),
        ("ImportError: cannot import name 'foo'", 1, DEPENDENCY),
        ("FileNotFoundError: No such file or directory", 1, FILE),
        ("Unauthorized: Invalid API key", 1, API),
        ("HTTP 403 Forbidden", 1, API),
        ("NOT NULL constraint failed", 1, SCHEMA),
        ("Unique constraint violated", 1, SCHEMA),
        ("IntegrityError: duplicate key", 1, SCHEMA),
        ("KeyError: 'variants'", 1, PARSING),
        ("AttributeError: 'NoneType' object has no attribute", 1, PARSING),
        ("JSONDecodeError: Expecting value", 1, PARSING),
        ("totally unrecognized error xyz123", 1, UNKNOWN),
    ]

    passed = 0
    failed = 0
    for stderr, exit_code, expected in cases:
        result = categorize_error(stderr, exit_code)
        actual = result["category"]
        if actual == expected:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: stderr={stderr!r:.50} exit={exit_code} "
                  f"expected={expected} got={actual}")

    total = passed + failed
    print(f"Self-test: {passed}/{total} passed" + (" - ALL PASS" if failed == 0 else " - FAILURES ABOVE"))
    if failed > 0:
        raise AssertionError(f"{failed} self-test(s) failed")


if __name__ == "__main__":
    _run_self_tests()
