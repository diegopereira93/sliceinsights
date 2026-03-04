"""
BR-First Catalog Seed — replaces seed_data_hybrid.py
Run: SEED_FORCE_CLEAR=true docker compose exec -e PYTHONPATH=/app backend_v3 \
     python -m app.db.seed_brazil_catalog
"""
import os
import re
from pathlib import Path
from decimal import Decimal

import pandas as pd
from sqlmodel import Session, select
from sqlalchemy import text

from app.db.database import sync_engine, init_db_sync
from app.models import Brand, PaddleMaster, MarketOffer


# --- Utilities ---

def normalize(text: str) -> str:
    if not text:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return re.sub(r"\s+", " ", text)


SOURCES = [
    ("data/raw/brazil_pickleball_store.csv", "Brazil Pickleball Store"),
    ("data/raw/pcklhouse_products.csv", "PCKL House"),
    ("data/raw/dropshot_brasil_products.csv", "Drop Shot Brasil"),
    ("data/raw/propadel_products.csv", "ProPadel"),
    ("data/raw/prospin_products.csv", "ProSpin"),
    ("data/raw/joola_brazil.csv", "Joola Brasil"),
    ("data/raw/yosports.csv", "yoSports"),
    ("data/raw/loja_supremo.csv", "Loja Supremo"),
    ("data/raw/shark.csv", "Shark"),
]

EXCLUDED = {"nan", "none", "unknown", "0", "n/a", ""}


def seed():
    init_db_sync()

    if os.getenv("SEED_FORCE_CLEAR", "false").lower() == "true":
        with Session(sync_engine) as s:
            s.execute(text("DELETE FROM market_offers"))
            s.execute(text("DELETE FROM paddle_master"))
            s.execute(text("DELETE FROM brands"))
            s.commit()
        print("🗑️  DB cleared")

    brands_cache: dict[str, Brand] = {}
    paddles_cache: dict[tuple, PaddleMaster] = {}

    with Session(sync_engine) as session:
        for csv_path, store_name in SOURCES:
            path = Path(csv_path)
            if not path.exists():
                print(f"  ⏩ {store_name}: not found")
                continue

            df = pd.read_csv(path)
            created = 0

            for _, row in df.iterrows():
                brand_name = str(row.get("brand_name", "")).strip().title()
                model_name = str(row.get("model_name", "")).strip()
                brand_key = normalize(brand_name)
                model_key = normalize(model_name)

                if brand_key in EXCLUDED or len(brand_key) < 2:
                    continue
                if not model_name or len(model_key) < 2:
                    continue

                # Get/create Brand
                if brand_key not in brands_cache:
                    existing_brands = session.exec(select(Brand)).all()
                    brand = next(
                        (b for b in existing_brands if normalize(b.name) == brand_key),
                        None,
                    )
                    if not brand:
                        brand = Brand(name=brand_name, website="")
                        session.add(brand)
                        session.flush()
                    brands_cache[brand_key] = brand
                brand = brands_cache[brand_key]

                # Skip non-paddles
                lower_model = model_name.lower()
                if any(x in lower_model for x in ["mala", "mochila", "bolsa", "capa", "rede", "kit", "bola", "ball", "tshirt", "camiseta", "raqueteira", "tênis", "tenis", "short", "meia"]):
                    continue
                if "raquete" not in lower_model and "paddle" not in lower_model:
                     # Some valid paddles might not have "raquete" in the CSV name, 
                     # but bags/accessories usually specify what they are.
                     # Let's keep brands we know are paddles if not clearly a bag.
                     pass

                # Get/create Paddle
                cache_key = (brand_key, model_key)
                if cache_key not in paddles_cache:
                    existing = session.exec(
                        select(PaddleMaster).where(
                            PaddleMaster.brand_id == brand.id,
                            PaddleMaster.model_name == model_name,
                        )
                    ).first()
                    if not existing:
                        image_url = str(row.get("image_url", "")) or None
                        
                        existing = PaddleMaster(
                            brand_id=brand.id,
                            model_name=model_name,
                            image_url=image_url,
                            available_in_brazil=True,
                            search_keywords=[brand_name.lower(), model_name.lower()],
                            specs_source="br_scraper",
                            specs_confidence=0.0
                        )
                        session.add(existing)
                        session.flush()
                        created += 1
                    paddles_cache[cache_key] = existing

                paddle = paddles_cache[cache_key]

                # Create MarketOffer
                price_raw = row.get("price_brl")
                if price_raw and str(price_raw) not in ("", "nan"):
                    try:
                        offer = MarketOffer(
                            paddle_id=paddle.id,
                            store_name=store_name,
                            price_brl=Decimal(str(float(price_raw))).quantize(
                                Decimal("0.01")
                            ),
                            url=str(row.get("product_url", "")),
                            is_active=True,
                        )
                        session.add(offer)
                    except Exception:
                        pass

            session.commit()
            print(f"  ✅ {store_name}: {created} new paddles")

    # Final audit
    with Session(sync_engine) as session:
        from sqlmodel import func

        total = session.exec(select(func.count(PaddleMaster.id))).one()
        br = session.exec(
            select(func.count(PaddleMaster.id)).where(
                PaddleMaster.available_in_brazil == True  # noqa: E712
            )
        ).one()
        img = session.exec(
            select(func.count(PaddleMaster.id)).where(
                PaddleMaster.image_url.is_not(None)
            )
        ).one()
        print(f"\n🏁 Final: {total} paddles | {br} in BR | {img} with images")


if __name__ == "__main__":
    seed()
