"""
Quality Aggregator — Phase 9 (QC-02, QC-03)

Computes and persists per-scraper quality metrics:
- freshness_hours: hours since newest MarketOffer.last_updated
- completeness_pct: % products with all required fields filled
- coverage_pct: % required fields filled across all products
- product_count: total active products for this scraper
- error_rate: fraction of runs in last 24h that failed

Run with:
  python scripts/quality_aggregator.py --scraper mercado_livre
  python scripts/quality_aggregator.py --all
  python scripts/quality_aggregator.py --consolidate
"""
import os
import sys
import argparse
import logging
import warnings
from pathlib import Path
from datetime import datetime, timezone, timedelta

warnings.filterwarnings("ignore")
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import sync_engine, init_db_sync
from sqlmodel import Session, select, func
from app.models.market_offer import MarketOffer
from app.models.quality_metric import QualityMetric
from app.models.store import Store


FRESHNESS_THRESHOLD_HOURS = 24.0
COMPLETENESS_THRESHOLD_PCT = 70.0
OFFER_REQUIRED_FIELDS = ["price_brl", "url", "store_id", "last_updated"]


def _now_utc() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


def _hours_ago(hours: int) -> datetime:
    """Return datetime N hours ago."""
    return _now_utc() - timedelta(hours=hours)


def compute_metrics(scraper_name: str, session: Session) -> dict:
    """Compute all 5 quality metrics for a given scraper."""
    now = _now_utc()
    
    store = session.exec(select(Store).where(Store.name == scraper_name)).first()
    if not store:
        return {
            "freshness_hours": float("inf"),
            "completeness_pct": 0.0,
            "coverage_pct": 0.0,
            "product_count": 0,
            "error_rate": 0.0,
            "status": "fail",
        }
    
    newest_row = session.exec(
        select(func.max(MarketOffer.last_updated))
        .where(MarketOffer.store_id == store.id, MarketOffer.is_active == True)
    ).one()

    if newest_row is None:
        freshness_hours = float("inf")
    else:
        if newest_row.tzinfo is None:
            newest_row = newest_row.replace(tzinfo=timezone.utc)
        freshness_hours = (now - newest_row).total_seconds() / 3600.0

    offers = session.exec(
        select(MarketOffer)
        .where(MarketOffer.store_id == store.id, MarketOffer.is_active == True)
    ).all()

    product_count = len(offers)

    if product_count == 0:
        completeness_pct = 0.0
        coverage_pct = 0.0
        error_rate = 0.0
    else:
        complete_rows = 0
        total_fields = 0
        filled_fields = 0

        for offer in offers:
            is_complete = True
            for field in OFFER_REQUIRED_FIELDS:
                val = getattr(offer, field, None)
                if val is None or (isinstance(val, str) and not val.strip()):
                    is_complete = False
                else:
                    filled_fields += 1
                total_fields += 1

            if is_complete:
                complete_rows += 1

        completeness_pct = (complete_rows / product_count * 100) if product_count > 0 else 0.0
        coverage_pct = (filled_fields / total_fields * 100) if total_fields > 0 else 0.0

        error_result = session.exec(
            select(func.count(QualityMetric.id))
            .where(
                QualityMetric.scraper_name == scraper_name,
                QualityMetric.checked_at >= _hours_ago(24),
                QualityMetric.status == "fail"
            )
        ).one()
        
        total_result = session.exec(
            select(func.count(QualityMetric.id))
            .where(
                QualityMetric.scraper_name == scraper_name,
                QualityMetric.checked_at >= _hours_ago(24)
            )
        ).one()

        if total_result and total_result > 0:
            error_rate = float(error_result or 0) / float(total_result)
        else:
            error_rate = 0.0

    status = "fail"
    if freshness_hours <= FRESHNESS_THRESHOLD_HOURS and completeness_pct >= COMPLETENESS_THRESHOLD_PCT and error_rate <= 0.3:
        status = "pass"

    return {
        "freshness_hours": freshness_hours,
        "completeness_pct": completeness_pct,
        "coverage_pct": coverage_pct,
        "product_count": product_count,
        "error_rate": error_rate,
        "status": status
    }


def persist_metrics(scraper_name: str, run_id: str, metrics: dict, session: Session) -> QualityMetric:
    """Create and commit a QualityMetric row."""
    metric = QualityMetric(
        scraper_name=scraper_name,
        run_id=run_id,
        freshness_hours=metrics["freshness_hours"],
        completeness_pct=metrics["completeness_pct"],
        coverage_pct=metrics["coverage_pct"],
        product_count=metrics["product_count"],
        error_rate=metrics["error_rate"],
        status=metrics["status"],
    )
    session.add(metric)
    session.commit()
    session.refresh(metric)
    return metric


def compute_and_persist(scraper_name: str, run_id: str, session: Session) -> QualityMetric:
    """Compute metrics and persist to database."""
    metrics = compute_metrics(scraper_name, session)
    return persist_metrics(scraper_name, run_id, metrics, session)


def consolidate(run_id: str, session: Session) -> dict:
    """Query all QualityMetric rows with matching run_id and compute summary."""
    rows = session.exec(
        select(QualityMetric)
        .where(QualityMetric.run_id == run_id)
    ).all()

    total = len(rows)
    passing = sum(1 for r in rows if r.status == "pass")
    failing = total - passing

    scrapers = {}
    for r in rows:
        fh = r.freshness_hours
        json_freshness = None if (fh is not None and fh != fh) else (None if fh == float("inf") else fh)
        scrapers[r.scraper_name] = {
            "freshness_hours": json_freshness,
            "completeness_pct": r.completeness_pct,
            "coverage_pct": r.coverage_pct,
            "product_count": r.product_count,
            "error_rate": r.error_rate,
            "status": r.status
        }

    summary_metric = QualityMetric(
        scraper_name="__consolidated__",
        run_id=run_id,
        freshness_hours=0.0,
        completeness_pct=0.0,
        coverage_pct=0.0,
        product_count=total,
        error_rate=failing / total if total > 0 else 0.0,
        status="pass" if failing == 0 else "fail",
        details={"total": total, "passing": passing, "failing": failing, "scrapers": scrapers}
    )
    session.add(summary_metric)
    session.commit()
    session.refresh(summary_metric)

    return {"total": total, "passing": passing, "failing": failing, "scrapers": scrapers}


def get_active_scrapers(session: Session) -> list[str]:
    """Get list of active scraper names from market_offers."""
    rows = session.exec(
        select(Store.name)
        .join(MarketOffer, MarketOffer.store_id == Store.id)
        .where(MarketOffer.is_active == True)
        .distinct()
    ).all()
    return list(rows)


def main():
    parser = argparse.ArgumentParser(description="Quality metric aggregator")
    parser.add_argument("--scraper", help="Single scraper name")
    parser.add_argument("--all", action="store_true", help="Run for all active scrapers")
    parser.add_argument("--consolidate", action="store_true", help="Consolidate results for this run")
    args = parser.parse_args()

    run_id = os.getenv("GITHUB_RUN_ID", "manual")

    init_db_sync()

    with Session(sync_engine) as session:
        if args.all:
            scrapers = get_active_scrapers(session)
            print(f"Running quality aggregation for {len(scrapers)} scrapers...")
            for scraper in scrapers:
                metric = compute_and_persist(scraper, run_id, session)
                print(f"  {scraper}: {metric.status} (freshness={metric.freshness_hours:.1f}h, completeness={metric.completeness_pct:.1f}%)")

        elif args.scraper:
            metric = compute_and_persist(args.scraper, run_id, session)
            print(f"{args.scraper}: {metric.status} (freshness={metric.freshness_hours:.1f}h, completeness={metric.completeness_pct:.1f}%)")

        elif args.consolidate:
            summary = consolidate(run_id, session)
            print(f"Consolidated: {summary['passing']}/{summary['total']} passing")


if __name__ == "__main__":
    main()
