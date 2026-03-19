"""
Scraper execution harness for SliceInsights health audit.

Orchestrates execution of all active scrapers in the Docker test environment,
captures complete execution metadata (stdout/stderr/exit_codes), categorizes
failures by root cause, and generates a status matrix.

Usage:
    python scripts/audit_runner.py [--output .audit/status_matrix.md] [--dry-run]
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add project root to sys.path so error_categorization is importable
_PROJECT_ROOT = Path(__file__).parent.parent
_AUDIT_DIR = _PROJECT_ROOT / ".audit"
sys.path.insert(0, str(_AUDIT_DIR))
import error_categorization  # noqa: E402

# ---------------------------------------------------------------------------
# Scraper registry
# ---------------------------------------------------------------------------
# All active scrapers discovered in scripts/ directory.
# Categories: shopify | playwright | csv | fetcher | specialized
# 11 primary scrapers (AUDIT-01 scope) + 4 secondary tools listed separately.
SCRAPERS = [
    # -- Shopify API scrapers (standardized, use scraper_utils.fetch_shopify_products) --
    {"script": "scrape_joola.py",       "category": "shopify"},
    {"script": "scrape_shark.py",       "category": "shopify"},
    {"script": "scrape_supremo.py",     "category": "shopify"},
    {"script": "scrape_yosports.py",    "category": "shopify"},
    {"script": "scrape_pcklhouse.py",   "category": "shopify"},
    {"script": "scrape_propadel.py",    "category": "shopify"},
    # -- Playwright async scrapers --
    {"script": "scrape_justpaddles.py", "category": "playwright"},
    # -- CSV ingestion batch scripts --
    {"script": "ingest_pb_studio_csv.py", "category": "csv"},
    {"script": "ingest_johnkew_csv.py",   "category": "csv"},
    # -- Specialized fetchers --
    {"script": "fetch_johnkew.py",      "category": "fetcher"},
    {"script": "fetch_pb_studio.py",    "category": "fetcher"},
]

# Secondary scripts (not in primary 11 scope but included for completeness)
SECONDARY_SCRAPERS = [
    {"script": "scrape_brazil_store.py",    "category": "shopify"},
    {"script": "scrape_dropshot_brasil.py", "category": "shopify"},
    {"script": "scrape_prospin.py",         "category": "shopify"},
    {"script": "scrape_product_specs.py",   "category": "specialized"},
]

TIMEOUT_SECONDS = 300  # 5 minutes per scraper maximum
LOG_FILE = _PROJECT_ROOT / ".audit" / "execution_log.json"
STATUS_FILE = _PROJECT_ROOT / ".audit" / "status_matrix.md"

# Max bytes to retain per stream to prevent JSON bloat
STREAM_TRUNCATE_BYTES = 5000


def run_scraper(script_name: str, dry_run: bool = False) -> dict:
    """
    Execute a single scraper via docker compose exec, capturing all metadata.

    Args:
        script_name: Filename within scripts/ (e.g. 'scrape_joola.py')
        dry_run: If True, skip actual execution and return mock SKIP result.

    Returns:
        Execution record dict with keys:
            script, exit_code, stdout, stderr, timestamp,
            status, error_category, error_reason, is_transient
    """
    timestamp = datetime.utcnow().isoformat()

    if dry_run:
        return {
            "script": script_name,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "timestamp": timestamp,
            "status": "SKIP",
            "error_category": "SKIP",
            "error_reason": "Dry run mode — execution skipped",
            "is_transient": False,
        }

    try:
        result = subprocess.run(
            [
                "docker", "compose", "exec", "-T",
                "backend_v3",
                "python", f"scripts/{script_name}",
            ],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=str(_PROJECT_ROOT),
        )

        stdout = result.stdout[:STREAM_TRUNCATE_BYTES]
        stderr = result.stderr[:STREAM_TRUNCATE_BYTES]
        error_cat = error_categorization.categorize_error(stderr, result.returncode)

        return {
            "script": script_name,
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "timestamp": timestamp,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "error_category": error_cat["category"],
            "error_reason": error_cat["reason"],
            "is_transient": error_cat["is_transient"],
            "matched_pattern": error_cat.get("matched_pattern"),
        }

    except subprocess.TimeoutExpired:
        return {
            "script": script_name,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "timestamp": timestamp,
            "status": "TIMEOUT",
            "error_category": "TIMEOUT",
            "error_reason": f"Scraper exceeded {TIMEOUT_SECONDS}s timeout",
            "is_transient": True,
            "matched_pattern": None,
        }

    except Exception as exc:  # pylint: disable=broad-except
        return {
            "script": script_name,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "timestamp": timestamp,
            "status": "ERROR",
            "error_category": "UNKNOWN",
            "error_reason": f"Harness error: {exc}",
            "is_transient": False,
            "matched_pattern": None,
        }


def run_all_scrapers(
    scraper_list: list[dict],
    dry_run: bool = False,
    include_secondary: bool = False,
) -> list[dict]:
    """
    Execute all scrapers sequentially and write execution_log.json.

    Args:
        scraper_list: List of scraper registry dicts (script + category).
        dry_run: Skip actual docker execution; produce SKIP records.
        include_secondary: Also run SECONDARY_SCRAPERS after primary list.

    Returns:
        List of execution record dicts.
    """
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    run_list = list(scraper_list)
    if include_secondary:
        run_list = run_list + SECONDARY_SCRAPERS

    print(
        f"Starting audit of {len(run_list)} scrapers at {datetime.utcnow().isoformat()}"
        f"{' [DRY RUN]' if dry_run else ''}"
    )

    execution_log: list[dict] = []
    for i, scraper_meta in enumerate(run_list, 1):
        script = scraper_meta["script"]
        category = scraper_meta.get("category", "unknown")
        print(f"  [{i}/{len(run_list)}] ({category}) {script} ...", end=" ", flush=True)

        record = run_scraper(script, dry_run=dry_run)
        # Attach category for richer reporting
        record["scraper_category"] = category
        execution_log.append(record)

        status_display = record["status"]
        cat_display = record.get("error_category", "N/A")
        print(f"{status_display} ({cat_display})")

    # Persist log
    with open(LOG_FILE, "w", encoding="utf-8") as fh:
        json.dump(execution_log, fh, indent=2)
    print(f"\nExecution log saved to {LOG_FILE}")

    # Summary counts
    pass_count = sum(1 for r in execution_log if r["status"] == "PASS")
    fail_count = sum(1 for r in execution_log if r["status"] == "FAIL")
    timeout_count = sum(1 for r in execution_log if r["status"] == "TIMEOUT")
    skip_count = sum(1 for r in execution_log if r["status"] == "SKIP")
    print(
        f"Results: {pass_count} PASS, {fail_count} FAIL, "
        f"{timeout_count} TIMEOUT, {skip_count} SKIP"
    )

    return execution_log


def generate_status_matrix(execution_log: list[dict]) -> str:
    """
    Generate a markdown status matrix from execution log entries.

    Returns:
        Markdown string with header metadata and result table.
    """
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    pass_count = sum(1 for r in execution_log if r["status"] == "PASS")
    fail_count = sum(1 for r in execution_log if r["status"] == "FAIL")
    timeout_count = sum(1 for r in execution_log if r["status"] == "TIMEOUT")

    lines = [
        "# Scraper Health Status Matrix",
        "",
        f"**Generated:** {now}  ",
        f"**Total:** {len(execution_log)} scrapers  ",
        f"**Results:** {pass_count} PASS / {fail_count} FAIL / {timeout_count} TIMEOUT",
        "",
        "| Scraper | Category | Status | Root Cause | Transient? | Last Run |",
        "|---------|----------|--------|------------|-----------|----------|",
    ]

    for entry in execution_log:
        script = entry["script"]
        cat = entry.get("scraper_category", entry.get("category", "unknown"))
        status = entry["status"]
        root_cause = entry.get("error_category", "N/A")
        transient = "Yes" if entry.get("is_transient") else "No"
        timestamp = (entry.get("timestamp") or "N/A")[:10]  # date portion only

        # Status emoji indicators for readability
        status_label = {
            "PASS": "PASS",
            "FAIL": "FAIL",
            "TIMEOUT": "TIMEOUT",
            "SKIP": "SKIP",
            "ERROR": "ERROR",
        }.get(status, status)

        lines.append(
            f"| {script} | {cat} | {status_label} | {root_cause} | {transient} | {timestamp} |"
        )

    # Failure breakdown section
    failures = [r for r in execution_log if r["status"] not in ("PASS", "SKIP")]
    if failures:
        lines += [
            "",
            "## Failure Details",
            "",
        ]
        for entry in failures:
            lines += [
                f"### {entry['script']} — {entry.get('error_category', 'UNKNOWN')}",
                "",
                f"- **Status:** {entry['status']}",
                f"- **Reason:** {entry.get('error_reason', 'N/A')}",
                f"- **Transient:** {'Yes (can retry)' if entry.get('is_transient') else 'No (requires fix)'}",
                f"- **Exit code:** {entry.get('exit_code', 'N/A')}",
                "",
            ]
            # Include last few lines of stderr if available
            stderr = (entry.get("stderr") or "").strip()
            if stderr:
                last_lines = "\n".join(stderr.splitlines()[-5:])
                lines += [
                    "```",
                    last_lines,
                    "```",
                    "",
                ]

    return "\n".join(lines)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SliceInsights scraper health audit harness"
    )
    parser.add_argument(
        "--output",
        default=str(STATUS_FILE),
        help="Output path for status matrix markdown (default: .audit/status_matrix.md)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip actual scraper execution; produce SKIP records for all",
    )
    parser.add_argument(
        "--include-secondary",
        action="store_true",
        help="Also run secondary scrapers (brazil_store, dropshot, etc.)",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Output path for execution_log.json (default: .audit/execution_log.json)",
    )
    args = parser.parse_args()

    # Override global log path if provided
    if args.log_file:
        global LOG_FILE  # noqa: PLW0603
        LOG_FILE = Path(args.log_file)

    execution_log = run_all_scrapers(
        SCRAPERS,
        dry_run=args.dry_run,
        include_secondary=args.include_secondary,
    )

    matrix = generate_status_matrix(execution_log)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(matrix)
    print(f"Status matrix saved to {output_path}")


if __name__ == "__main__":
    main()
