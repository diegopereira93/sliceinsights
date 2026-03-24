"""
Seed the 10 correct Store records into the database.
Usage: python scripts/seed_stores.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select

from app.db.database import sync_engine
from app.models.store import Store
from app.models.market_offer import MarketOffer

STORES = [
    {"name": "Joola Brasil", "slug": "joola-brasil", "base_url": "https://joola.com.br"},
    {"name": "Shark", "slug": "shark", "base_url": "https://sharkbeachtennis.com.br"},
    {"name": "Loja Supremo", "slug": "loja-supremo", "base_url": "https://lojasupremo.com.br"},
    {"name": "yoSports", "slug": "yosports", "base_url": "https://yosports.com.br"},
    {"name": "PCKL House", "slug": "pcklhouse", "base_url": "https://pcklhouse.com.br"},
    {"name": "ProPadel", "slug": "propadel", "base_url": "https://lojapropadel.com.br"},
    {"name": "Just Paddles", "slug": "just-paddles", "base_url": "https://justpaddles.com.br"},
    {
        "name": "Brazil Pickleball Store",
        "slug": "brazil-pickleball-store",
        "base_url": "https://brazilpickleballstore.com.br",
    },
    {"name": "Drop Shot Brasil", "slug": "drop-shot-brasil", "base_url": "https://dropshot.com.br"},
    {"name": "ProSpin", "slug": "prospin", "base_url": "https://prospin.com.br"},
]

STALE_NAMES = {
    "Test Store",
    "Pickleball Central",
    "PB Village",
    "Net2Court",
    "JustPaddles",
    "ProPadel",
    "propadel",
    "justpaddles",
}


def main():
    with Session(sync_engine) as session:
        stale = session.exec(select(Store).where(Store.name.in_(STALE_NAMES))).all()
        stale_ids = [s.id for s in stale]

        if stale_ids:
            for mo in session.exec(
                select(MarketOffer).where(MarketOffer.store_id.in_(stale_ids))
            ).all():
                session.delete(mo)
            print(f"  Deleted market_offers for stale stores")
            for s in stale:
                print(f"  Deleted stale store: {s.name}")
                session.delete(s)
            session.commit()

        for data in STORES:
            existing = session.exec(select(Store).where(Store.name == data["name"])).first()
            if existing:
                print(f"  Exists: {data['name']}")
                continue
            store = Store(**data)
            session.add(store)
            print(f"  Created: {data['name']}")

        session.commit()

        all_stores = session.exec(select(Store)).all()
        print(f"\nTotal stores: {len(all_stores)}")
        for s in all_stores:
            print(f"  - {s.name}")


if __name__ == "__main__":
    main()
