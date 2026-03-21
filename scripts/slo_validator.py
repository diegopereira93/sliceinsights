"""
SLO Validation Engine — Phase 6 (SLO-03, SLO-04, SLO-05)

Checks freshness (market_offers) and completeness (paddle_master) against
configured thresholds and writes pass/fail results to slo_logs.

Usage:
  python scripts/slo_validator.py --all
  python scripts/slo_validator.py --scraper mercado_livre
"""
import sys
import argparse
import logging
import warnings
from pathlib import Path
from datetime import datetime, timezone

warnings.filterwarnings("ignore")
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import sync_engine, init_db_sync
from sqlmodel import Session, select, func
from app.models.market_offer import MarketOffer
from app.models.paddle import PaddleMaster
from app.models.slo import SLOLog
from app.models.store import Store
from scripts.slo_config import FRESHNESS_SLO_HOURS, COMPLETENESS_SLO_HOURS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_utc() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def _make_aware(dt: datetime) -> datetime:
    """Attach UTC timezone to a naive datetime."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _hours_since(dt: datetime) -> float:
    """Return elapsed hours since *dt* (UTC). Returns infinity if dt is None."""
    if dt is None:
        return float("inf")
    dt = _make_aware(dt)
    return (_now_utc() - dt).total_seconds() / 3600.0


# ---------------------------------------------------------------------------
# Freshness check  (SLO-03)
# ---------------------------------------------------------------------------

def check_freshness(session: Session, scraper_name: str | None = None) -> list[SLOLog]:
    """Check that market_offers were updated within FRESHNESS_SLO_HOURS.

    Groups by store. If *scraper_name* is provided, filters to that store.

    Status logic:
      - SKIP: No data yet (scraper never ran)
      - PASS: Data exists and was updated within SLO window (< 24h)
      - FAIL: Data exists but hasn't been updated for > 24h (violated SLO)

    Writes one SLOLog row per store and returns the list of written logs.
    """
    query = (
        select(
            Store.name,
            func.max(MarketOffer.last_updated).label("newest"),
        )
        .join(Store, MarketOffer.store_id == Store.id)
        .where(MarketOffer.is_active == True)
        .group_by(Store.name)
    )
    if scraper_name is not None:
        query = query.where(Store.name == scraper_name)

    rows = session.exec(query).all()

    logs: list[SLOLog] = []

    if not rows:
        target = scraper_name if scraper_name is not None else "__all__"
        log = SLOLog(
            scraper_name=target,
            metric_type="freshness",
            value_hours=float("inf"),
            threshold_hours=float(FRESHNESS_SLO_HOURS),
            status="skip",
            details={"reason": "no_data_yet"},
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        logs.append(log)
        print(f"[freshness] {target}: SKIP (no data yet)")
        return logs

    for row in rows:
        store_name = row.name
        newest = _make_aware(row.newest)
        age_hours = _hours_since(newest)

        # Determine status:
        # - If data was updated in last 24h → PASS (within SLO)
        # - If data is older than 24h → FAIL (violated SLO)
        if age_hours < FRESHNESS_SLO_HOURS:
            status = "pass"
            reason = "within_slo"
        else:
            status = "fail"
            reason = "stale_data"

        details: dict = {
            "reason": reason,
            "newest_record": str(newest) if newest else None,
            "age_hours": round(age_hours, 2) if age_hours != float("inf") else None,
        }
        log = SLOLog(
            scraper_name=store_name,
            metric_type="freshness",
            value_hours=age_hours if age_hours != float("inf") else 99999.0,
            threshold_hours=float(FRESHNESS_SLO_HOURS),
            status=status,
            details=details,
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        logs.append(log)
        age_str = f"{age_hours:.1f}h" if age_hours != float("inf") else "N/A"
        print(f"[freshness] {store_name}: {status.upper()} (age={age_str}, threshold={FRESHNESS_SLO_HOURS}h, reason={reason})")

    return logs


# ---------------------------------------------------------------------------
# Completeness check  (SLO-04)
# ---------------------------------------------------------------------------

def check_completeness(session: Session, scraper_name: str | None = None) -> SLOLog:
    """Check that paddle_master records were updated within COMPLETENESS_SLO_HOURS.

    *scraper_name* is accepted for API symmetry but paddle_master is a global
    catalog — the check always covers all rows. The scraper_name written to the
    log is the caller-supplied value or '__all__'.

    Status logic:
      - SKIP: No data yet (catalog never populated)
      - SKIP: Data exists but was just updated < 24h ago (still in progress)
      - FAIL: Data exists but hasn't been updated for > 7 days (violated SLO)

    Writes one SLOLog row and returns it.
    """
    target = scraper_name if scraper_name is not None else "__all__"

    newest_updated_at = session.exec(
        select(func.max(PaddleMaster.updated_at))
    ).one_or_none()

    # session.exec(...).one_or_none() returns the scalar directly for single-column
    newest = newest_updated_at if newest_updated_at else None
    newest = _make_aware(newest) if newest else None
    age_hours = _hours_since(newest)

    # Determine status:
    if newest is None:
        # No data at all — catalog never populated. Skip (don't fail).
        status = "skip"
        reason = "no_data_yet"
    elif age_hours < FRESHNESS_SLO_HOURS:
        # Data was updated recently (< 24h) → scraper is actively running. Skip.
        status = "skip"
        reason = "recently_updated"
    elif age_hours <= COMPLETENESS_SLO_HOURS:
        # Data is old but within SLO window. Pass.
        status = "pass"
        reason = "within_slo"
    else:
        # Data is too old. Fail.
        status = "fail"
        reason = "stale_data"

    details: dict = {
        "reason": reason,
        "newest_updated_at": str(newest) if newest else None,
        "age_hours": round(age_hours, 2) if age_hours != float("inf") else None,
    }

    log = SLOLog(
        scraper_name=target,
        metric_type="completeness",
        value_hours=age_hours if age_hours != float("inf") else 99999.0,
        threshold_hours=float(COMPLETENESS_SLO_HOURS),
        status=status,
        details=details,
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    age_str = f"{age_hours:.1f}h" if age_hours != float("inf") else "N/A"
    print(f"[completeness] {target}: {status.upper()} (age={age_str}, threshold={COMPLETENESS_SLO_HOURS}h, reason={reason})")
    return log


# ---------------------------------------------------------------------------
# Real-time hook  (SLO-01 / SLO-05)
# ---------------------------------------------------------------------------

def validate_job_slo(scraper_name: str) -> None:
    """Non-blocking real-time SLO validation hook for scrapers.

    Call this at the end of any scraper's main() after committing data.
    Failures are logged to slo_logs but never raise exceptions.
    """
    try:
        init_db_sync()
        with Session(sync_engine) as session:
            check_freshness(session, scraper_name=scraper_name)
    except Exception as exc:
        print(f"[WARN] SLO validation failed (non-blocking): {exc}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run SLO validation checks against the production database."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        dest="run_all",
        help="Run all checks for all scrapers.",
    )
    group.add_argument(
        "--scraper",
        metavar="NAME",
        help="Run checks for a specific scraper / store name.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    sync_engine.echo = False
    init_db_sync()

    scraper_name = None if args.run_all else args.scraper

    with Session(sync_engine) as session:
        check_freshness(session, scraper_name=scraper_name)
        check_completeness(session, scraper_name=scraper_name)

    print("[slo_validator] Done.")


if __name__ == "__main__":
    main()
