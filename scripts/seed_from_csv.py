"""
Seed database from CSV files in data/db/.
Used by init-db.sh on docker-compose up.

Usage: python scripts/seed_from_csv.py [--force]
  --force  Re-import all CSV rows (default: skip existing)
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
from datetime import datetime
from sqlmodel import Session, select
from app.db.database import sync_engine
from app.models.brand import Brand
from app.models.store import Store
from app.models.paddle import PaddleMaster
from app.models.market_offer import MarketOffer


def bulk_seed_stores(csv_path: Path, session: Session) -> dict:
    if not csv_path.exists():
        print("  stores.csv not found, skipping")
        return {}

    existing = {s.name: s for s in session.exec(select(Store)).all()}
    created = 0
    for row in csv.DictReader(open(csv_path)):
        name = row.get("name", "").strip()
        slug = row.get("slug", "").strip() or None
        base_url = row.get("base_url", "").strip()
        if name and base_url and name not in existing:
            session.add(Store(name=name, slug=slug, base_url=base_url))
            created += 1
    session.commit()
    return {s.name: s.id for s in session.exec(select(Store)).all()}


def bulk_seed_brands(csv_path: Path, session: Session) -> dict:
    if not csv_path.exists():
        return {}

    existing = {b.name: b for b in session.exec(select(Brand)).all()}
    for row in csv.DictReader(open(csv_path)):
        name = row.get("name", "").strip()
        if name and name not in existing:
            session.add(Brand(name=name))
    session.commit()
    return {b.name: b.id for b in session.exec(select(Brand)).all()}


def bulk_seed_paddles(csv_path: Path, session: Session, brand_map: dict) -> dict:
    if not csv_path.exists():
        print("  paddle_master.csv not found, skipping paddles")
        return {}

    existing = {}
    for p in session.exec(select(PaddleMaster)).all():
        key = (p.brand_id, p.model_name)
        existing[key] = p

    brand_name_to_id = {b.name: b.id for b in session.exec(select(Brand)).all()}
    created = 0
    for row in csv.DictReader(open(csv_path)):
        brand_name = row.get("brand_name", "").strip()
        model_name = row.get("model_name", "").strip()
        if not brand_name or not model_name:
            continue
        if brand_name not in brand_name_to_id:
            brand = Brand(name=brand_name)
            session.add(brand)
            session.flush()
            brand_name_to_id[brand_name] = brand.id
            brand_map[brand_name] = brand.id
        brand_id = brand_name_to_id[brand_name]
        key = (brand_id, model_name)
        if key not in existing:
            session.add(PaddleMaster(
                brand_id=brand_id,
                model_name=model_name,
                image_url=row.get("image_url", "").strip() or None,
                available_in_brazil=True,
            ))
            created += 1
    session.commit()

    return {(p.brand_id, p.model_name): p.id
            for p in session.exec(select(PaddleMaster)).all()}


def bulk_seed_offers(csv_path: Path, session: Session, paddle_map: dict) -> int:
    if not csv_path.exists():
        print("  market_offers.csv not found, skipping offers")
        return 0

    store_map = {s.name: s.id for s in session.exec(select(Store)).all()}
    existing = {(str(o.paddle_id), o.store_id): o
                for o in session.exec(select(MarketOffer)).all()}

    created = 0
    for row in csv.DictReader(open(csv_path)):
        brand_name = row.get("brand_name", "").strip()
        model_name = row.get("model_name", "").strip()
        store_name = row.get("store_name", "").strip()
        if not brand_name or not model_name or not store_name:
            continue

        brand_id = None
        for bid, bname in session.exec(select(Brand.id, Brand.name)).all():
            if bname == brand_name:
                brand_id = bid
                break
        if brand_id is None:
            continue

        key = (brand_id, model_name)
        if key not in paddle_map:
            continue
        paddle_id = paddle_map[key]
        if store_name not in store_map:
            continue
        store_id = store_map[store_name]

        price_str = row.get("price_brl", "0").strip()
        try:
            price = Decimal(price_str.replace(",", "."))
        except Exception:
            continue
        if price <= 0:
            continue

        url = row.get("url", "").strip()
        offer_key = (str(paddle_id), store_id)
        if offer_key in existing:
            offer = existing[offer_key]
            offer.price_brl = price
            offer.url = url
            offer.last_updated = datetime.utcnow()
            session.add(offer)
        else:
            session.add(MarketOffer(
                paddle_id=paddle_id,
                store_id=store_id,
                price_brl=price,
                url=url,
                is_active=True,
            ))
            created += 1
            existing[offer_key] = True
    session.commit()
    return created


def main():
    db_dir = Path(__file__).parent.parent / "data" / "db"

    if not any(db_dir.glob("*.csv")):
        print(f"No CSV files in {db_dir}, skipping CSV seed")
        return

    print("Seeding from CSV files...")

    with Session(sync_engine) as session:
        store_map = bulk_seed_stores(db_dir / "stores.csv", session)
        print(f"  Stores: {len(store_map)} total")
        brand_map = bulk_seed_brands(db_dir / "brands.csv", session)
        print(f"  Brands: {len(brand_map)} total")
        paddle_map = bulk_seed_paddles(db_dir / "paddle_master.csv", session, brand_map)
        print(f"  Paddles: {len(paddle_map)} total")
        n_created = bulk_seed_offers(db_dir / "market_offers.csv", session, paddle_map)
        print(f"  New offers: {n_created}")

    print("CSV seed complete!")


if __name__ == "__main__":
    main()
