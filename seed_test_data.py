"""
Seed script for local development database.

Usage:
  docker compose up -d postgres_v3  # Start local DB on port 5434
  DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5434/picklematch" \
    DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5434/picklematch" \
    .venv/bin/python seed_test_data.py
"""

import asyncio
from decimal import Decimal
from uuid import uuid4

from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import async_engine
from app.models.brand import Brand
from app.models.paddle import PaddleMaster
from app.models.market_offer import MarketOffer
from app.models.store import Store
from app.models.enums import FaceMaterial, PaddleShape


async def seed():
    async with AsyncSession(async_engine) as session:
        brands_data = [
            {"name": "Selkirk", "website": "https://www.selkirk.com"},
            {"name": "Joola", "website": "https://www.joolasports.com"},
            {"name": "Onix", "website": "https://www.onixpickleball.com"},
            {"name": "Engage", "website": "https://www.engagepickleball.com"},
            {"name": "Franklin", "website": "https://www.franklinpickleball.com"},
        ]
        brands = {}
        for bd in brands_data:
            brand = Brand(**bd)
            session.add(brand)
            await session.flush()
            brands[bd["name"]] = brand

        stores_data = [
            {
                "name": "ProPadel",
                "slug": "propadel",
                "base_url": "https://propadel.com.br",
                "is_active": True,
                "available_brands": ["Selkirk", "Joola"],
            },
            {
                "name": "JustPaddles",
                "slug": "justpaddles",
                "base_url": "https://www.justpaddles.com.br",
                "is_active": True,
                "available_brands": ["Selkirk", "Onix", "Engage"],
            },
            {
                "name": "Pickleball Central",
                "slug": "pickleball-central",
                "base_url": "https://pickleballcentral.com.br",
                "is_active": True,
                "available_brands": ["Franklin", "Onix"],
            },
            {
                "name": "PB Village",
                "slug": "pb-village",
                "base_url": "https://pbvillage.com.br",
                "is_active": True,
                "available_brands": ["Joola", "Engage"],
            },
            {
                "name": "Net2Court",
                "slug": "net2court",
                "base_url": "https://net2court.com.br",
                "is_active": True,
                "available_brands": ["Selkirk", "Franklin"],
            },
        ]
        stores = {}
        for sd in stores_data:
            store = Store(**sd)
            session.add(store)
            await session.flush()
            stores[sd["slug"]] = store

        paddles_data = [
            {
                "model_name": "Invikta Air",
                "brand": brands["Selkirk"],
                "face_material": FaceMaterial.CARBON,
                "shape": PaddleShape.ELONGATED,
                "core_thickness_mm": 16.0,
                "core_material": "Polymer Honeycomb",
                "weight_grams": 227.0,
                "swing_weight": 115,
                "twist_weight": 6.5,
                "spin_rpm": 1900,
                "power_rating": 8,
                "handle_length": "5.5",
                "grip_circumference": "4.25",
                "image_url": "https://images.unsplash.com/photo-1554068865-24cecd4e6b8f?w=400",
                "available_in_brazil": True,
                "specs_source": "seed",
            },
            {
                "model_name": "Scoop Alpha",
                "brand": brands["Joola"],
                "face_material": FaceMaterial.CARBON,
                "shape": PaddleShape.STANDARD,
                "core_thickness_mm": 13.0,
                "core_material": "Polymer Honeycomb",
                "weight_grams": 220.0,
                "swing_weight": 110,
                "twist_weight": 6.2,
                "spin_rpm": 2100,
                "power_rating": 7,
                "handle_length": "5.0",
                "grip_circumference": "4.125",
                "image_url": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400",
                "available_in_brazil": True,
                "specs_source": "seed",
            },
            {
                "model_name": "Perseus Pro",
                "brand": brands["Onix"],
                "face_material": FaceMaterial.FIBERGLASS,
                "shape": PaddleShape.ELONGATED,
                "core_thickness_mm": 14.0,
                "core_material": "Polymer Honeycomb",
                "weight_grams": 235.0,
                "swing_weight": 120,
                "twist_weight": 7.0,
                "spin_rpm": 1800,
                "power_rating": 9,
                "handle_length": "5.5",
                "grip_circumference": "4.25",
                "image_url": "https://images.unsplash.com/photo-1584464491033-06628f3a6b7b?w=400",
                "available_in_brazil": True,
                "specs_source": "seed",
            },
            {
                "model_name": "Pursuit Pro",
                "brand": brands["Engage"],
                "face_material": FaceMaterial.CARBON,
                "shape": PaddleShape.STANDARD,
                "core_thickness_mm": 16.0,
                "core_material": "Polymer Honeycomb",
                "weight_grams": 225.0,
                "swing_weight": 112,
                "twist_weight": 6.3,
                "spin_rpm": 1950,
                "power_rating": 7,
                "handle_length": "5.25",
                "grip_circumference": "4.125",
                "image_url": "https://images.unsplash.com/photo-1535131749006-b7f58c99034b?w=400",
                "available_in_brazil": True,
                "specs_source": "seed",
            },
            {
                "model_name": "XLS Franklin",
                "brand": brands["Franklin"],
                "face_material": FaceMaterial.FIBERGLASS,
                "shape": PaddleShape.ELONGATED,
                "core_thickness_mm": 13.0,
                "core_material": "Polymer Honeycomb",
                "weight_grams": 230.0,
                "swing_weight": 118,
                "twist_weight": 6.8,
                "spin_rpm": 1700,
                "power_rating": 8,
                "handle_length": "5.0",
                "grip_circumference": "4.25",
                "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
                "available_in_brazil": True,
                "specs_source": "seed",
            },
        ]

        store_slug_list = list(stores.keys())

        paddle_store_combinations = [
            (0, "propadel", 1099.00),
            (0, "justpaddles", 1149.00),
            (0, "pb-village", 1199.00),
            (1, "propadel", 899.00),
            (1, "pickleball-central", 949.00),
            (2, "justpaddles", 1299.00),
            (2, "net2court", 1399.00),
            (3, "propadel", 1049.00),
            (3, "pb-village", 999.00),
            (4, "pickleball-central", 799.00),
            (4, "net2court", 849.00),
        ]

        for idx, pdata in enumerate(paddles_data):
            paddle = PaddleMaster(
                model_name=pdata["model_name"],
                brand_id=pdata["brand"].id,
                face_material=pdata["face_material"],
                shape=pdata["shape"],
                core_thickness_mm=pdata["core_thickness_mm"],
                core_material=pdata["core_material"],
                weight_grams=pdata["weight_grams"],
                swing_weight=pdata["swing_weight"],
                twist_weight=pdata["twist_weight"],
                spin_rpm=pdata["spin_rpm"],
                power_rating=pdata["power_rating"],
                handle_length=pdata["handle_length"],
                grip_circumference=pdata["grip_circumference"],
                image_url=pdata["image_url"],
                available_in_brazil=pdata["available_in_brazil"],
                specs_source=pdata["specs_source"],
                search_keywords=[pdata["model_name"].lower().split()[0]],
            )
            session.add(paddle)
            await session.flush()

            for paddle_idx, store_slug, price in paddle_store_combinations:
                if paddle_idx == idx:
                    offer = MarketOffer(
                        paddle_id=paddle.id,
                        store_id=stores[store_slug].id,
                        price_brl=Decimal(str(price)),
                        url=f"{stores[store_slug].base_url}/paddle/{paddle.id}",
                        is_active=True,
                    )
                    session.add(offer)

        await session.commit()
        print(
            f"Seeded {len(brands)} brands, {len(stores)} stores, {len(paddles_data)} paddles, {len(paddle_store_combinations)} offers"
        )


if __name__ == "__main__":
    asyncio.run(seed())
