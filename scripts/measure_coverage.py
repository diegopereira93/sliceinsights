"""
Per-Scraper Coverage Report — Phase 2 (QUAL-05)

Counts unique paddles and total offers per store_name in market_offers.

Run with:
  docker compose exec -T backend_v3 python scripts/measure_coverage.py
"""
import sys, json, logging, warnings
from pathlib import Path

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
            func.count(MarketOffer.paddle_id.distinct()).label("unique_paddles"),
            func.count(MarketOffer.id).label("total_offers"),
        )
        .where(MarketOffer.is_active == True)
        .group_by(MarketOffer.store_name)
        .order_by(func.count(MarketOffer.id).desc())
    ).all()

results = []
for r in rows:
    results.append({
        "store_name": r.store_name,
        "unique_paddles": r.unique_paddles,
        "total_offers": r.total_offers,
    })

total_paddles = sum(r["unique_paddles"] for r in results)
total_offers = sum(r["total_offers"] for r in results)
results.append({
    "store_name": "_TOTAL",
    "unique_paddles": total_paddles,
    "total_offers": total_offers,
})

print(json.dumps(results, indent=2, default=str))
