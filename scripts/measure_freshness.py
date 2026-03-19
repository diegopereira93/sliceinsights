"""
Data Freshness Report — Phase 2 (AUDIT-05)

Measures per-source data age by querying min/max last_updated from market_offers.

Run with:
  docker compose exec -T backend_v3 python scripts/measure_freshness.py
"""
import sys, json, logging, warnings
from pathlib import Path
from datetime import datetime, timezone

warnings.filterwarnings("ignore")
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.db.database import sync_engine, init_db_sync
from sqlmodel import Session, select, func
from app.models.market_offer import MarketOffer

sync_engine.echo = False

init_db_sync()
with Session(sync_engine) as session:
    rows = session.exec(
        select(
            MarketOffer.store_name,
            func.count(MarketOffer.id).label("offer_count"),
            func.min(MarketOffer.last_updated).label("oldest_record"),
            func.max(MarketOffer.last_updated).label("newest_record"),
        )
        .where(MarketOffer.is_active == True)
        .group_by(MarketOffer.store_name)
        .order_by(func.min(MarketOffer.last_updated))
    ).all()

now = datetime.now(timezone.utc)
results = []
for r in rows:
    oldest = r.oldest_record
    newest = r.newest_record
    if oldest and oldest.tzinfo is None:
        oldest = oldest.replace(tzinfo=timezone.utc)
    if newest and newest.tzinfo is None:
        newest = newest.replace(tzinfo=timezone.utc)
    age_days = (now - oldest).days if oldest else None
    freshness_days = (now - newest).days if newest else None
    results.append({
        "store_name": r.store_name,
        "offer_count": r.offer_count,
        "oldest_record": str(r.oldest_record),
        "newest_record": str(r.newest_record),
        "age_days": age_days,
        "freshness_days": freshness_days,
    })

print(json.dumps(results, indent=2, default=str))
