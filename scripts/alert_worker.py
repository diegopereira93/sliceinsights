"""
SLO Alert Worker -- Phase 7 (ALT-01 through ALT-05)

Queries slo_logs for recent FAIL entries, applies dedup throttle,
and dispatches alerts via Telegram, GitHub Issues, and Email.

Supports both PostgreSQL and Firestore backends.

Usage:
  python scripts/alert_worker.py --all
  python scripts/alert_worker.py --scraper mercado_livre
"""
import os
import sys
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings

settings = get_settings()

USE_FIRESTORE = os.getenv("USE_FIRESTORE", "").lower() in ("true", "1", "yes") or settings.use_firestore

if USE_FIRESTORE:
    from google.cloud.firestore import Client
    from app.db.firestore_client import init_firestore_sync
    from app.db.firestore_slo import (
        get_recent_slo_failures,
        get_recent_slo_passes,
        should_send_alert_firestore,
        upsert_alert_state,
        clear_alert_throttle as clear_throttle_firestore,
    )
    from app.models.slo_alert import SLOBreach
else:
    from sqlmodel import Session, select
    from app.db.database import sync_engine, init_db_sync
    from app.models.slo import SLOLog
    from app.models.slo_alert import SLOBreach
    from app.services.slo_alerts import (
        SLOAlertService, get_slo_alert_service,
        should_send_alert, upsert_alert_record, clear_alert_throttle,
    )

logger = logging.getLogger(__name__)
LOOKBACK_HOURS = 7
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def slo_log_to_breach(log) -> SLOBreach:
    """Convert a SLOLog to a SLOBreach dataclass for alerting."""
    checked_at_str = (
        log.checked_at.strftime("%Y-%m-%dT%H:%M:%SZ") if log.checked_at else "unknown"
    )
    details = log.details if hasattr(log, 'details') else getattr(log, 'details', {})
    last_record = details.get("newest_record") or details.get("newest_updated_at")
    return SLOBreach(
        scraper_name=log.scraper_name,
        metric_type=log.metric_type,
        value_hours=log.value_hours,
        threshold_hours=log.threshold_hours,
        checked_at=checked_at_str,
        last_record_time=last_record,
        details=details,
    )


def process_failures_postgres(session, failures, service) -> dict:
    """Process failures with PostgreSQL backend."""
    stats = {"processed": 0, "sent": 0, "throttled": 0, "errors": 0}
    for log in failures:
        stats["processed"] += 1
        if not should_send_alert(session, log.scraper_name, log.metric_type):
            print(f"[alert_worker] THROTTLED: {log.scraper_name}/{log.metric_type}")
            stats["throttled"] += 1
            continue
        breach = slo_log_to_breach(log)
        try:
            results = service.notify(breach)
            upsert_alert_record(session, log.scraper_name, log.metric_type)
            sent_channels = [ch for ch, ok in results.items() if ok]
            print(
                f"[alert_worker] SENT {breach.severity}: "
                f"{log.scraper_name}/{log.metric_type} -> {sent_channels}"
            )
            stats["sent"] += 1
        except Exception as exc:
            logger.warning(f"[alert_worker] ERROR dispatching {log.scraper_name}: {exc}")
            stats["errors"] += 1
    return stats


async def process_failures_firestore(firestore_client, failures, service) -> dict:
    """Process failures with Firestore backend."""
    stats = {"processed": 0, "sent": 0, "throttled": 0, "errors": 0}
    for log in failures:
        stats["processed"] += 1
        if not await should_send_alert_firestore(firestore_client, log.scraper_name, log.metric_type):
            print(f"[alert_worker] THROTTLED: {log.scraper_name}/{log.metric_type}")
            stats["throttled"] += 1
            continue
        breach = slo_log_to_breach(log)
        try:
            results = service.notify(breach)
            await upsert_alert_state(firestore_client, log.scraper_name, log.metric_type)
            sent_channels = [ch for ch, ok in results.items() if ok]
            print(
                f"[alert_worker] SENT {breach.severity}: "
                f"{log.scraper_name}/{log.metric_type} -> {sent_channels}"
            )
            stats["sent"] += 1
        except Exception as exc:
            logger.warning(f"[alert_worker] ERROR dispatching {log.scraper_name}: {exc}")
            stats["errors"] += 1
    return stats


def process_passes_postgres(session, passes) -> int:
    """Clear throttle for each unique scraper+metric that has returned to passing."""
    cleared = 0
    seen: set[tuple[str, str]] = set()
    for log in passes:
        key = (log.scraper_name, log.metric_type)
        if key in seen:
            continue
        seen.add(key)
        clear_alert_throttle(session, log.scraper_name, log.metric_type)
        cleared += 1
    if cleared:
        print(f"[alert_worker] Cleared {cleared} resolved throttle(s)")
    return cleared


async def process_passes_firestore(firestore_client, passes) -> int:
    """Clear throttle for each unique scraper+metric that has returned to passing."""
    cleared = 0
    seen: set[tuple[str, str]] = set()
    for log in passes:
        key = (log.scraper_name, log.metric_type)
        if key in seen:
            continue
        seen.add(key)
        await clear_throttle_firestore(firestore_client, log.scraper_name, log.metric_type)
        cleared += 1
    if cleared:
        print(f"[alert_worker] Cleared {cleared} resolved throttle(s)")
    return cleared


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Query slo_logs for breaches and dispatch alerts."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        dest="run_all",
        help="Process all recent breaches.",
    )
    group.add_argument(
        "--scraper",
        metavar="NAME",
        help="Process breaches for a specific scraper.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    scraper_name = None if args.run_all else args.scraper

    logging.basicConfig(level=logging.INFO)
    service = get_slo_alert_service()

    if USE_FIRESTORE:
        import asyncio
        asyncio.run(main_firestore(scraper_name, service))
    else:
        main_postgres(scraper_name, service)


def main_firestore(scraper_name, service):
    """Main entry point for Firestore backend."""
    async def run():
        for attempt in range(MAX_RETRIES):
            try:
                firestore_client = init_firestore_sync()
                break
            except Exception as exc:
                if attempt < MAX_RETRIES - 1:
                    print(f"[alert_worker] Firestore connection attempt {attempt + 1}/{MAX_RETRIES} failed: {exc}")
                    print(f"[alert_worker] Retrying in {RETRY_DELAY_SECONDS}s...")
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    print(f"[alert_worker] ERROR: Failed to connect to Firestore after {MAX_RETRIES} attempts: {exc}")
                    sys.exit(1)
        
        from google.cloud.firestore import AsyncClient
        async_client = AsyncClient()
        
        failures = await get_recent_slo_failures(async_client, lookback_hours=LOOKBACK_HOURS, scraper_name=scraper_name)
        print(f"[alert_worker] Found {len(failures)} failure(s) in last {LOOKBACK_HOURS}h")
        
        stats = await process_failures_firestore(async_client, failures, service)
        print(f"[alert_worker] Stats: {stats}")
        
        passes = await get_recent_slo_passes(async_client, lookback_hours=LOOKBACK_HOURS, scraper_name=scraper_name)
        await process_passes_firestore(async_client, passes)
        
        print("[alert_worker] Done.")
    
    import asyncio
    asyncio.run(run())


def main_postgres(scraper_name, service):
    """Main entry point for PostgreSQL backend."""
    db_url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL")
    if not db_url:
        print("[alert_worker] ERROR: DATABASE_URL_SYNC or DATABASE_URL environment variable is required")
        sys.exit(1)

    for attempt in range(MAX_RETRIES):
        try:
            init_db_sync()
            break
        except Exception as exc:
            if attempt < MAX_RETRIES - 1:
                print(f"[alert_worker] Connection attempt {attempt + 1}/{MAX_RETRIES} failed: {exc}")
                print(f"[alert_worker] Retrying in {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"[alert_worker] ERROR: Failed to initialize database after {MAX_RETRIES} attempts: {exc}")
                sys.exit(1)

    with Session(sync_engine) as session:
        from sqlmodel import select
        from app.models.slo import SLOLog
        
        cutoff = datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)
        stmt = (
            select(SLOLog)
            .where(SLOLog.status == "fail")
            .where(SLOLog.checked_at >= cutoff)
            .order_by(SLOLog.checked_at.desc())
        )
        if scraper_name is not None:
            stmt = stmt.where(SLOLog.scraper_name == scraper_name)
        failures = list(session.exec(stmt).all())
        
        print(f"[alert_worker] Found {len(failures)} failure(s) in last {LOOKBACK_HOURS}h")
        
        stats = process_failures_postgres(session, failures, service)
        print(f"[alert_worker] Stats: {stats}")
        
        stmt = (
            select(SLOLog)
            .where(SLOLog.status.in_(["pass", "skip"]))
            .where(SLOLog.checked_at >= cutoff)
            .order_by(SLOLog.checked_at.desc())
        )
        if scraper_name is not None:
            stmt = stmt.where(SLOLog.scraper_name == scraper_name)
        passes = list(session.exec(stmt).all())
        
        process_passes_postgres(session, passes)

    print("[alert_worker] Done.")


if __name__ == "__main__":
    main()
