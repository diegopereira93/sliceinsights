"""
Pre-Deploy Validation — Phase 8 (DEP-01, DEP-02, DEP-05)

Dual validation before publishing a batch to production:
  1. SLO gate — re-checks slo_logs for the batch calendar day
  2. Corruption audit — scans market_offers_staging for NULL critical fields

Usage:
  python scripts/deploy_validator.py --validate-batch batch_20260319_2f4a8
  python scripts/deploy_validator.py --validate-batch batch_20260319_2f4a8 --batch-date 2026-03-19
"""
import sys
import argparse
import logging
import warnings
from pathlib import Path
from datetime import date, datetime, timezone

warnings.filterwarnings("ignore")
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.database import sync_engine


# ---------------------------------------------------------------------------
# SLO Gate
# ---------------------------------------------------------------------------

def check_slo_gate(session: Session, batch_date: date) -> tuple[list[str], list[str]]:
    """Query slo_logs for the calendar day window and return (passed_scrapers, failed_scrapers).

    Looks at entries where checked_at is within batch_date 00:00:00 UTC to 23:59:59 UTC.
    Excludes the synthetic '__all__' scraper name.
    """
    day_start = datetime(batch_date.year, batch_date.month, batch_date.day, 0, 0, 0, tzinfo=timezone.utc)
    day_end = datetime(batch_date.year, batch_date.month, batch_date.day, 23, 59, 59, tzinfo=timezone.utc)

    passed_result = session.execute(
        text(
            "SELECT DISTINCT scraper_name FROM slo_logs "
            "WHERE checked_at >= :day_start AND checked_at <= :day_end "
            "AND status = 'pass' AND scraper_name != '__all__'"
        ),
        {"day_start": day_start, "day_end": day_end},
    )
    passed_scrapers = [row.scraper_name for row in passed_result.fetchall()]

    failed_result = session.execute(
        text(
            "SELECT DISTINCT scraper_name FROM slo_logs "
            "WHERE checked_at >= :day_start AND checked_at <= :day_end "
            "AND status = 'fail' AND scraper_name != '__all__'"
        ),
        {"day_start": day_start, "day_end": day_end},
    )
    failed_scrapers = [row.scraper_name for row in failed_result.fetchall()]

    return passed_scrapers, failed_scrapers


# ---------------------------------------------------------------------------
# Corruption Audit
# ---------------------------------------------------------------------------

def run_corruption_audit(session: Session, batch_id: str) -> tuple[bool, list[str]]:
    """Scan market_offers_staging for data integrity issues in the given batch.

    Checks:
      a. Total rows — fail if 0 (empty batch)
      b. Rows with NULL price_brl
      c. Rows with NULL url
      d. Rows with NULL store_name
      e. Rows with NULL paddle_id

    Returns (passed: bool, failures: list[str]).
    """
    failures: list[str] = []

    # a. Total row count
    total = session.execute(
        text("SELECT COUNT(*) FROM market_offers_staging WHERE batch_id = :b"),
        {"b": batch_id},
    ).scalar()

    if not total:
        return False, [f"Empty batch: no rows in staging for batch_id '{batch_id}'"]

    # b. NULL price_brl
    null_price = session.execute(
        text("SELECT COUNT(*) FROM market_offers_staging WHERE batch_id = :b AND price_brl IS NULL"),
        {"b": batch_id},
    ).scalar()
    if null_price:
        failures.append(f"Corruption: {null_price} rows with NULL price_brl in batch '{batch_id}'")

    # c. NULL url
    null_url = session.execute(
        text("SELECT COUNT(*) FROM market_offers_staging WHERE batch_id = :b AND url IS NULL"),
        {"b": batch_id},
    ).scalar()
    if null_url:
        failures.append(f"Corruption: {null_url} rows with NULL url in batch '{batch_id}'")

    # d. NULL store_name
    null_store = session.execute(
        text("SELECT COUNT(*) FROM market_offers_staging WHERE batch_id = :b AND store_name IS NULL"),
        {"b": batch_id},
    ).scalar()
    if null_store:
        failures.append(f"Corruption: {null_store} rows with NULL store_name in batch '{batch_id}'")

    # e. NULL paddle_id
    null_paddle = session.execute(
        text("SELECT COUNT(*) FROM market_offers_staging WHERE batch_id = :b AND paddle_id IS NULL"),
        {"b": batch_id},
    ).scalar()
    if null_paddle:
        failures.append(f"Corruption: {null_paddle} rows with NULL paddle_id in batch '{batch_id}'")

    return len(failures) == 0, failures


# ---------------------------------------------------------------------------
# Combined Pre-Deploy Validation
# ---------------------------------------------------------------------------

def run_pre_deploy_validation(batch_id: str, batch_date: date) -> tuple[bool, list[str]]:
    """Run full pre-deploy validation: SLO gate + corruption audit.

    Args:
        batch_id: Identifier for the batch (e.g. 'batch_20260319_2f4a8')
        batch_date: Calendar date of the batch run (used for SLO log window)

    Returns:
        (passed: bool, failures: list[str])
    """
    all_failures: list[str] = []

    with Session(sync_engine) as session:
        # 1. SLO gate
        passed_scrapers, failed_scrapers = check_slo_gate(session, batch_date)
        if failed_scrapers:
            for scraper in failed_scrapers:
                all_failures.append(f"SLO freshness check failed: {scraper}")

        # 2. Corruption audit
        audit_ok, audit_failures = run_corruption_audit(session, batch_id)
        all_failures.extend(audit_failures)

    return len(all_failures) == 0, all_failures


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run pre-deploy validation: SLO gate re-check + corruption audit."
    )
    parser.add_argument(
        "--validate-batch",
        metavar="BATCH_ID",
        required=True,
        help="Batch ID to validate (e.g. batch_20260319_2f4a8).",
    )
    parser.add_argument(
        "--batch-date",
        metavar="YYYY-MM-DD",
        default=None,
        help="Calendar date of the batch run (default: today UTC).",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.batch_date:
        batch_date = date.fromisoformat(args.batch_date)
    else:
        batch_date = datetime.now(timezone.utc).date()

    print(f"[deploy_validator] Validating batch '{args.validate_batch}' for date {batch_date} ...")

    ok, failures = run_pre_deploy_validation(args.validate_batch, batch_date)

    if ok:
        print("[deploy_validator] PASS — batch is clean and SLOs met.")
        sys.exit(0)
    else:
        print("[deploy_validator] FAIL — validation errors:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
