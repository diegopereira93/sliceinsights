"""
Deploy Worker — Phase 8 (DEP-01, DEP-03, DEP-04, DEP-05)

Core deploy pipeline: batch aggregation from slo_logs into staging,
atomic publish with version tagging, flag-flip rollback,
force-publish override, and deploy audit logging.

Usage:
  python scripts/deploy_worker.py --run
  python scripts/deploy_worker.py --run --batch-date 2026-03-19
  python scripts/deploy_worker.py --validate-batch batch_20260319_2f4a8
  python scripts/deploy_worker.py --force-publish batch_20260319_2f4a8 --operator-id admin
  python scripts/deploy_worker.py --rollback batch_20260319_2f4a8
"""
import argparse
import hashlib
import logging
import sys
import warnings
from pathlib import Path
from datetime import date, datetime, timezone, timedelta

warnings.filterwarnings("ignore")
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import sync_engine
from app.models.deploy_log import DeployLog
from app.services.slo_alerts import SLOAlertService
from scripts.deploy_validator import run_pre_deploy_validation, check_slo_gate

logger = logging.getLogger("deploy_worker")


# ---------------------------------------------------------------------------
# Batch ID and version helpers
# ---------------------------------------------------------------------------

def generate_batch_id(batch_date: date) -> str:
    """Generate a human-readable batch identifier.

    Format: batch_YYYYMMDD_<6 hex chars>
    The 6-char suffix is derived from the current UTC timestamp hash.
    """
    suffix = hashlib.md5(
        str(datetime.now(timezone.utc)).encode()
    ).hexdigest()[:6]
    return f"batch_{batch_date.strftime('%Y%m%d')}_{suffix}"


def get_next_version_id(conn) -> int:
    """Return the next version_id for a publish operation.

    Queries deploy_logs for the highest published version_id.
    Returns 1 if no previous deploys exist.
    """
    result = conn.execute(
        text(
            "SELECT COALESCE(MAX(version_id), 0) + 1 FROM deploy_logs "
            "WHERE status = 'published'"
        )
    )
    return result.scalar()


# ---------------------------------------------------------------------------
# Staging helpers
# ---------------------------------------------------------------------------

def cleanup_old_staging(conn, days: int = 7) -> int:
    """Delete staging rows older than `days` days (TTL cleanup).

    Returns count of deleted rows.
    """
    result = conn.execute(
        text(
            "DELETE FROM market_offers_staging "
            "WHERE created_at < NOW() - INTERVAL ':days days'"
        ),
        {"days": days},
    )
    return result.rowcount


def aggregate_batch(
    conn,
    batch_id: str,
    batch_date: date,
    passed_scrapers: list[str],
) -> tuple[int, list[str]]:
    """Insert market_offers rows into staging for each SLO-passing scraper.

    Scopes to the calendar day: [batch_date 00:00:00 UTC, batch_date+1 00:00:00 UTC).

    Returns:
        (total_rows_inserted, list_of_scrapers_included)
    """
    if not passed_scrapers:
        return 0, []

    day_start = datetime(
        batch_date.year, batch_date.month, batch_date.day, 0, 0, 0,
        tzinfo=timezone.utc,
    )
    day_end = day_start + timedelta(days=1)

    total = 0
    included: list[str] = []

    for scraper_name in passed_scrapers:
        result = conn.execute(
            text(
                "INSERT INTO market_offers_staging "
                "  (batch_id, paddle_id, store_name, price_brl, url, last_updated) "
                "SELECT :batch_id, paddle_id, store_name, price_brl, url, last_updated "
                "FROM market_offers "
                "WHERE store_name = :scraper_name "
                "  AND last_updated >= :day_start "
                "  AND last_updated < :day_end "
                "  AND is_active = true"
            ),
            {
                "batch_id": batch_id,
                "scraper_name": scraper_name,
                "day_start": day_start,
                "day_end": day_end,
            },
        )
        total += result.rowcount
        included.append(scraper_name)

    return total, included


# ---------------------------------------------------------------------------
# Publish and prune
# ---------------------------------------------------------------------------

def publish_batch(conn, batch_id: str, version_id: int) -> int:
    """Atomically publish staging rows to market_offers with the given version_id.

    Steps:
      a. Mark previous version inactive.
      b. Upsert from staging into market_offers (ON CONFLICT paddle_id+store_name).

    Returns:
        Number of rows upserted.
    """
    prev_version = version_id - 1

    # a. Deactivate previous version
    conn.execute(
        text(
            "UPDATE market_offers SET is_active = false "
            "WHERE version_id = :prev_version"
        ),
        {"prev_version": prev_version},
    )

    # b. Upsert from staging
    result = conn.execute(
        text(
            "INSERT INTO market_offers "
            "  (paddle_id, store_name, price_brl, url, last_updated, is_active, version_id) "
            "SELECT paddle_id, store_name, price_brl, url, last_updated, true, :version_id "
            "FROM market_offers_staging "
            "WHERE batch_id = :batch_id "
            "ON CONFLICT (paddle_id, store_name) "
            "DO UPDATE SET "
            "  price_brl = EXCLUDED.price_brl, "
            "  url = EXCLUDED.url, "
            "  last_updated = EXCLUDED.last_updated, "
            "  version_id = EXCLUDED.version_id, "
            "  is_active = true"
        ),
        {"batch_id": batch_id, "version_id": version_id},
    )
    return result.rowcount


def prune_old_versions(conn, current_version_id: int) -> int:
    """Delete market_offers rows older than keep window (current + 1 previous).

    keep_min = current_version_id - 1
    Rows with version_id < keep_min are removed.

    Returns:
        Count of deleted rows.
    """
    keep_min = current_version_id - 1
    result = conn.execute(
        text(
            "DELETE FROM market_offers "
            "WHERE version_id IS NOT NULL "
            "  AND version_id < :keep_min"
        ),
        {"keep_min": keep_min},
    )
    return result.rowcount


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

def rollback_batch(batch_id: str) -> None:
    """Roll back a published batch by flipping is_active flags.

    Looks up version_id from deploy_logs for the given batch_id,
    then:
      - Sets is_active=false for current version
      - Sets is_active=true for previous version (current - 1)

    Writes a DeployLog entry with status='rolled_back'.
    """
    with sync_engine.begin() as conn:
        # Look up the current version_id from the published deploy log
        row = conn.execute(
            text(
                "SELECT version_id FROM deploy_logs "
                "WHERE batch_id = :batch_id AND status = 'published' "
                "ORDER BY id DESC LIMIT 1"
            ),
            {"batch_id": batch_id},
        ).fetchone()

        if row is None:
            logger.error(
                f"[deploy_worker] No published deploy log found for batch '{batch_id}'"
            )
            print(f"[deploy_worker] ERROR: No published batch found for '{batch_id}'")
            return

        current_version = row.version_id
        previous_version = current_version - 1

        # Flip active flags
        conn.execute(
            text(
                "UPDATE market_offers SET is_active = false "
                "WHERE version_id = :current"
            ),
            {"current": current_version},
        )
        conn.execute(
            text(
                "UPDATE market_offers SET is_active = true "
                "WHERE version_id = :previous"
            ),
            {"previous": previous_version},
        )

    # Write audit log
    with Session(sync_engine) as session:
        log_entry = DeployLog(
            batch_id=batch_id,
            version_id=current_version,
            status="rolled_back",
            scrapers_passed=0,
            finished_at=datetime.now(timezone.utc),
        )
        session.add(log_entry)
        session.commit()

    print(
        f"[deploy_worker] Rollback complete: "
        f"batch '{batch_id}' (v{current_version}) -> v{previous_version} restored"
    )


# ---------------------------------------------------------------------------
# Force publish
# ---------------------------------------------------------------------------

def force_publish(batch_id: str, operator_id: str) -> None:
    """Force-publish a batch, bypassing validation.

    Sets forced=True and operator_id in DeployLog.
    Sends a Telegram alert (failure is non-fatal).
    """
    with sync_engine.begin() as conn:
        version_id = get_next_version_id(conn)
        product_count = publish_batch(conn, batch_id=batch_id, version_id=version_id)

    # Write audit log
    with Session(sync_engine) as session:
        log_entry = DeployLog(
            batch_id=batch_id,
            version_id=version_id,
            status="published",
            scrapers_passed=0,
            products_published=product_count,
            forced=True,
            operator_id=operator_id,
            finished_at=datetime.now(timezone.utc),
        )
        session.add(log_entry)
        session.commit()

    # Alert — non-fatal
    try:
        service = SLOAlertService()
        service.send_telegram(
            f"FORCE PUBLISH: batch {batch_id} by {operator_id}"
        )
    except Exception:
        logger.warning("[deploy_worker] Failed to send force-publish alert")

    print(
        f"[deploy_worker] Force-publish complete: "
        f"batch '{batch_id}' published as v{version_id} "
        f"by '{operator_id}' ({product_count} products)"
    )


# ---------------------------------------------------------------------------
# Main deploy pipeline
# ---------------------------------------------------------------------------

def run_deploy(batch_date: date | None = None) -> None:
    """Orchestrate the full nightly deploy pipeline.

    Steps:
      a. Generate batch_id
      b. Run SLO gate to get passed scrapers
      c. Clean old staging rows (TTL 7 days)
      d. Aggregate batch into staging
      e. Write DeployLog status='pending'
      f. Run pre-deploy validation
      g. Update DeployLog to status='validated' (or 'failed')
      h. Publish batch
      i. Update DeployLog to status='published'
      j. Prune old versions
    """
    if batch_date is None:
        batch_date = datetime.now(timezone.utc).date()

    batch_id = generate_batch_id(batch_date)
    print(f"[deploy_worker] Starting deploy: batch_id={batch_id}, date={batch_date}")

    with sync_engine.begin() as conn:
        # b. SLO gate
        with Session(sync_engine) as session:
            passed_scrapers, failed_scrapers = check_slo_gate(session, batch_date)

        if not passed_scrapers:
            logger.error(
                f"[deploy_worker] No scrapers passed SLO gate for {batch_date}. "
                f"Failed: {failed_scrapers}"
            )
            print(f"[deploy_worker] ABORT: No scrapers passed SLO gate for {batch_date}")
            sys.exit(1)

        print(
            f"[deploy_worker] SLO gate: {len(passed_scrapers)} passed, "
            f"{len(failed_scrapers)} failed"
        )

        # c. Cleanup old staging
        cleanup_old_staging(conn, days=7)

        # d. Aggregate
        total_rows, included_scrapers = aggregate_batch(
            conn, batch_id=batch_id, batch_date=batch_date,
            passed_scrapers=passed_scrapers,
        )
        print(
            f"[deploy_worker] Aggregated {total_rows} rows "
            f"from {len(included_scrapers)} scraper(s) into staging"
        )

        # e. Get version_id and write pending log
        version_id = get_next_version_id(conn)

    with Session(sync_engine) as session:
        deploy_log = DeployLog(
            batch_id=batch_id,
            version_id=version_id,
            status="pending",
            scrapers_passed=len(passed_scrapers),
        )
        session.add(deploy_log)
        session.commit()
        deploy_log_id = deploy_log.id

    # f. Validation
    ok, failures = run_pre_deploy_validation(batch_id, batch_date)

    with Session(sync_engine) as session:
        entry = session.get(DeployLog, deploy_log_id)
        if not ok:
            if entry:
                entry.status = "failed"
                entry.failure_reason = "; ".join(failures)
                entry.finished_at = datetime.now(timezone.utc)
                session.add(entry)
                session.commit()
            print("[deploy_worker] FAIL: Validation failed:")
            for f in failures:
                print(f"  - {f}")
            sys.exit(1)

        # g. Update to validated
        if entry:
            entry.status = "validated"
            session.add(entry)
            session.commit()

    print("[deploy_worker] Validation passed. Publishing...")

    # h. Publish
    with sync_engine.begin() as conn:
        product_count = publish_batch(conn, batch_id=batch_id, version_id=version_id)
        # j. Prune old versions
        pruned = prune_old_versions(conn, current_version_id=version_id)

    # i. Update to published
    with Session(sync_engine) as session:
        entry = session.get(DeployLog, deploy_log_id)
        if entry:
            entry.status = "published"
            entry.products_published = product_count
            entry.finished_at = datetime.now(timezone.utc)
            session.add(entry)
            session.commit()

    print(
        f"[deploy_worker] Deploy complete: "
        f"batch '{batch_id}' v{version_id} — "
        f"{product_count} products published, "
        f"{pruned} old rows pruned"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deploy worker — nightly batch aggregation and publish pipeline."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--run",
        action="store_true",
        help="Run full nightly deploy pipeline.",
    )
    group.add_argument(
        "--validate-batch",
        metavar="BATCH_ID",
        dest="validate_batch",
        help="Re-run pre-deploy validation only for a given batch.",
    )
    group.add_argument(
        "--force-publish",
        metavar="BATCH_ID",
        dest="force_publish",
        help="Force-publish a batch bypassing validation.",
    )
    group.add_argument(
        "--rollback",
        metavar="BATCH_ID",
        help="Roll back a specific published batch.",
    )
    parser.add_argument(
        "--batch-date",
        metavar="YYYY-MM-DD",
        dest="batch_date",
        default=None,
        help="Override batch date (default: today UTC). Format: YYYY-MM-DD.",
    )
    parser.add_argument(
        "--operator-id",
        metavar="NAME",
        dest="operator_id",
        default="unknown",
        help="Operator identifier for force-publish audit trail.",
    )
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = _build_parser()
    args = parser.parse_args()

    batch_date = None
    if args.batch_date:
        batch_date = date.fromisoformat(args.batch_date)

    try:
        if args.run:
            run_deploy(batch_date=batch_date)

        elif args.validate_batch:
            bd = batch_date or datetime.now(timezone.utc).date()
            print(
                f"[deploy_worker] Validating batch '{args.validate_batch}' "
                f"for date {bd} ..."
            )
            from scripts.deploy_validator import run_pre_deploy_validation
            ok, failures = run_pre_deploy_validation(args.validate_batch, bd)
            if ok:
                print("[deploy_worker] PASS — batch is clean and SLOs met.")
            else:
                print("[deploy_worker] FAIL — validation errors:")
                for f in failures:
                    print(f"  - {f}")
                sys.exit(1)

        elif args.force_publish:
            force_publish(args.force_publish, operator_id=args.operator_id)

        elif args.rollback:
            rollback_batch(args.rollback)

    except SystemExit:
        raise
    except Exception as exc:
        logger.error(f"[deploy_worker] Unexpected error: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
