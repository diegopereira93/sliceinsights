import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlmodel import Session, select

from app.models.brand import Brand
from app.models.market_offer import MarketOffer
from app.models.paddle import PaddleMaster
from app.models.store import Store

EXCLUDED = {"nan", "none", "unknown", "0", "n/a", ""}

SKIP_KEYWORDS = [
    "mala", "mochila", "bolsa", "capa", "rede", "kit", "bola", "ball",
    "tshirt", "camiseta", "raqueteira", "tenis", "short", "meia",
    "grip", "overgrip", "munhequeira", "acessorio",
    "vestuario", "bone", "viseira", "bag", "backpack",
    "shoes", "apparel", "glove", "socks", "hat", "visor",
]


def normalize(text: str) -> str:
    """Normalize whitespace and title-case a string."""
    return re.sub(r"\s+", " ", text.strip()).title()


def is_paddle(row: dict) -> bool:
    """Return True if the row represents a paddle (not an accessory)."""
    model = row.get("model_name", "").lower()
    brand = row.get("brand_name", "").lower()
    combined = f"{brand} {model}"
    return not any(kw in combined for kw in SKIP_KEYWORDS)


def ingest_rows(
    rows: list[dict],
    store_id: int,
    session: Session,
) -> dict:
    """
    Ingest scraped product rows into the database.

    Each row dict must have keys: brand_name, model_name, price_brl, product_url, image_url (optional).
    Non-paddle items are filtered out via is_paddle().
    Brands and PaddleMasters are deduplicated (get-or-create).
    MarketOffers are upserted by (paddle_id, store_id).

    Returns: {"created": int, "updated": int, "skipped": int}
    """
    stats = {"created": 0, "updated": 0, "skipped": 0}

    for row in rows:
        if not is_paddle(row):
            stats["skipped"] += 1
            continue

        brand_name = row.get("brand_name", "").strip()
        model_name = row.get("model_name", "").strip()
        price_str = str(row.get("price_brl", "0"))
        product_url = row.get("product_url", "")
        image_url = row.get("image_url", "")

        if not brand_name or brand_name.lower() in EXCLUDED:
            stats["skipped"] += 1
            continue
        if not model_name or model_name.lower() in EXCLUDED:
            stats["skipped"] += 1
            continue

        try:
            price = Decimal(price_str.replace(",", "."))
            if price <= 0:
                stats["skipped"] += 1
                continue
        except (InvalidOperation, ValueError):
            stats["skipped"] += 1
            continue

        brand_name = normalize(brand_name)
        model_name = normalize(model_name)

        brand = session.exec(
            select(Brand).where(Brand.name == brand_name)
        ).first()
        if not brand:
            brand = Brand(name=brand_name)
            session.add(brand)
            session.flush()

        paddle = session.exec(
            select(PaddleMaster).where(
                PaddleMaster.brand_id == brand.id,
                PaddleMaster.model_name == model_name,
            )
        ).first()
        if not paddle:
            paddle = PaddleMaster(
                brand_id=brand.id,
                model_name=model_name,
                image_url=image_url or None,
            )
            session.add(paddle)
            session.flush()

        existing_offer = session.exec(
            select(MarketOffer).where(
                MarketOffer.paddle_id == paddle.id,
                MarketOffer.store_id == store_id,
            )
        ).first()
        if existing_offer:
            existing_offer.price_brl = price
            existing_offer.url = product_url
            existing_offer.is_active = True
            existing_offer.last_updated = datetime.utcnow()
            session.add(existing_offer)
            stats["updated"] += 1
        else:
            offer = MarketOffer(
                paddle_id=paddle.id,
                store_id=store_id,
                price_brl=price,
                url=product_url,
                is_active=True,
            )
            session.add(offer)
            stats["created"] += 1

    return stats
