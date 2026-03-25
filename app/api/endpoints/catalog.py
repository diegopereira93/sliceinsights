from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import any_

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.database import get_session
from app.models import PaddleMaster, MarketOffer, Brand
from app.models.store import Store
from app.models.enums import FaceMaterial

router = APIRouter(prefix="/catalog", tags=["catalog"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/paddles")
@limiter.limit("100/minute")
async def list_catalog_paddles(
    request: Request,
    core_thickness: Optional[List[float]] = Query(default=None),
    surface_material: Optional[List[FaceMaterial]] = Query(default=None),
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    brand: Optional[str] = None,
    store: Optional[str] = None,
    limit: int = Query(default=50, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    offer_subq = (
        select(
            MarketOffer.paddle_id,
            func.min(MarketOffer.price_brl).label("min_price"),
        )
        .where(MarketOffer.is_active.is_(True))
        .group_by(MarketOffer.paddle_id)
        .subquery()
    )

    base_query = (
        select(PaddleMaster, offer_subq.c.min_price)
        .options(
            selectinload(PaddleMaster.brand),
            selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store),
        )
        .join(offer_subq, PaddleMaster.id == offer_subq.c.paddle_id)
    )

    if core_thickness:
        base_query = base_query.where(PaddleMaster.core_thickness_mm.in_(core_thickness))

    if surface_material:
        base_query = base_query.where(
            PaddleMaster.face_material.in_([m.value for m in surface_material])
        )

    if price_min is not None:
        base_query = base_query.where(offer_subq.c.min_price >= price_min)

    if price_max is not None:
        base_query = base_query.where(offer_subq.c.min_price <= price_max)

    if brand:
        base_query = base_query.join(Brand, PaddleMaster.brand_id == Brand.id).where(
            Brand.name.ilike(f"%{brand}%")
        )

    if store:
        base_query = (
            base_query.join(MarketOffer, PaddleMaster.id == MarketOffer.paddle_id)
            .join(Store, MarketOffer.store_id == Store.id)
            .where(Store.slug == store)
        )

    count_query = select(func.count(PaddleMaster.id)).select_from(offer_subq)
    if core_thickness:
        count_query = count_query.where(PaddleMaster.core_thickness_mm.in_(core_thickness))
    if surface_material:
        count_query = count_query.where(
            PaddleMaster.face_material.in_([m.value for m in surface_material])
        )
    if price_min is not None:
        count_query = count_query.where(offer_subq.c.min_price >= price_min)
    if price_max is not None:
        count_query = count_query.where(offer_subq.c.min_price <= price_max)
    if brand:
        count_query = count_query.join(Brand, PaddleMaster.brand_id == Brand.id).where(
            Brand.name.ilike(f"%{brand}%")
        )
    if store:
        count_query = (
            count_query.join(MarketOffer, PaddleMaster.id == MarketOffer.paddle_id)
            .join(Store, MarketOffer.store_id == Store.id)
            .where(Store.slug == store)
        )

    count_result = await session.exec(count_query)
    total = count_result.first() or 0

    query = base_query.order_by(offer_subq.c.min_price.asc()).offset(offset).limit(limit)
    result = await session.exec(query)
    rows = result.all()

    data = []
    for paddle, min_price in rows:
        active_offers = [o for o in paddle.market_offers if o.is_active]
        data.append(
            {
                "id": str(paddle.id),
                "brand": paddle.brand.name if paddle.brand else None,
                "model_name": paddle.model_name,
                "image_url": paddle.image_url,
                "price": min_price,
                "specs": {
                    "core_thickness_mm": paddle.core_thickness_mm,
                    "surface_material": paddle.face_material.value
                    if paddle.face_material
                    else None,
                },
                "market_offers": sorted(
                    [
                        {
                            "store_name": o.store.name,
                            "price_brl": float(o.price_brl),
                            "store_url": o.url,
                        }
                        for o in active_offers
                    ],
                    key=lambda x: x["price_brl"],
                ),
            }
        )

    return {"data": data, "total": total, "limit": limit, "offset": offset}


@router.get("/stores")
@limiter.limit("100/minute")
async def list_catalog_stores(
    request: Request,
    brand: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    query = select(Store).where(Store.is_active.is_(True))

    if brand:
        query = query.where(brand == any_(Store.available_brands))

    result = await session.exec(query)
    stores = result.all()

    data = [
        {
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
            "base_url": s.base_url,
            "is_active": s.is_active,
            "available_brands": s.available_brands or [],
        }
        for s in stores
    ]

    return {"data": data, "total": len(data)}
