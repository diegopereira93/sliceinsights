"""
FastAPI routes for PickleMatch Advisor API.
"""
import hashlib
import json
from typing import Optional
from uuid import UUID

from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from thefuzz import fuzz
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.database import get_session
from app.models import Brand, PaddleMaster, MarketOffer
from app.models.paddle import PaddleRead
from app.models.brand import BrandRead
from app.models.market_offer import MarketOfferRead
from app.schemas.user_profile import RecommendationRequest, RecommendationResult, UserProfile
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# TTL caches for frequently accessed data
_brands_cache = TTLCache(maxsize=1, ttl=300)  # 5 min cache for brands
_paddles_cache = TTLCache(maxsize=50, ttl=60)  # 1 min cache for paddle queries


# ============== Health ==============

@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    """Health check endpoint with database validation."""
    try:
        from sqlalchemy import text
        await session.exec(text("SELECT 1"))
        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")


# ============== Brands ==============

@router.get("/brands", response_model=dict)
async def list_brands(session: AsyncSession = Depends(get_session)):
    """List all brands (cached for 5 minutes)."""
    cache_key = "all_brands"
    
    # Check cache first
    if cache_key in _brands_cache:
        return _brands_cache[cache_key]
    
    result = await session.exec(select(Brand))
    brands = result.all()
    response = {
        "data": [BrandRead.model_validate(b) for b in brands],
        "total": len(brands)
    }
    
    # Store in cache
    _brands_cache[cache_key] = response
    return response


# ============== Paddles ==============

@router.get("/paddles", response_model=dict)
@limiter.limit("100/minute")
async def list_paddles(
    request: Request,
    brand_id: Optional[int] = None,
    skill_level: Optional[str] = None,
    is_featured: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    session: AsyncSession = Depends(get_session)
):
    """List paddles with optional filters. Optimized to avoid N+1 queries."""
    from sqlalchemy import literal_column
    
    # Create subquery for market offer aggregations
    offer_subq = (
        select(
            MarketOffer.paddle_id,
            func.min(MarketOffer.price_brl).label("min_price"),
            func.count(MarketOffer.id).label("offer_count")
        )
        .where(MarketOffer.is_active == True)
        .group_by(MarketOffer.paddle_id)
        .subquery()
    )
    
    # Main query joining paddles with offer aggregations
    query = (
        select(
            PaddleMaster,
            offer_subq.c.min_price,
            offer_subq.c.offer_count
        )
        .options(selectinload(PaddleMaster.brand))
        .outerjoin(offer_subq, PaddleMaster.id == offer_subq.c.paddle_id)
    )
    
    # Apply filters
    if brand_id:
        query = query.where(PaddleMaster.brand_id == brand_id)
    if skill_level:
        query = query.where(PaddleMaster.skill_level == skill_level)
    if is_featured is not None:
        query = query.where(PaddleMaster.is_featured == is_featured)
    if min_price is not None:
        query = query.where(offer_subq.c.min_price >= min_price)
    if max_price is not None:
        query = query.where(offer_subq.c.min_price <= max_price)
    
    query = query.offset(offset).limit(limit)
    result = await session.exec(query)
    rows = result.all()
    
    # Build paddle data from single query results
    paddle_data = []
    for row in rows:
        paddle = row[0]
        min_price_val = row[1]
        offer_count = row[2] or 0
        
        paddle_data.append(
            PaddleRead.from_paddle(
                paddle,
                min_price=float(min_price_val) if min_price_val else None,
                offers_count=offer_count
            )
        )
    
    # Count total (without pagination)
    count_query = select(func.count(PaddleMaster.id))
    if brand_id:
        count_query = count_query.where(PaddleMaster.brand_id == brand_id)
    if skill_level:
        count_query = count_query.where(PaddleMaster.skill_level == skill_level)
    if is_featured is not None:
        count_query = count_query.where(PaddleMaster.is_featured == is_featured)
    
    total_result = await session.exec(count_query)
    total = total_result.first() or 0
    
    return {
        "data": paddle_data,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/paddles/{paddle_id}")
async def get_paddle(
    paddle_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """Get paddle details with market offers."""
    result = await session.exec(
        select(PaddleMaster)
        .options(selectinload(PaddleMaster.brand))
        .where(PaddleMaster.id == paddle_id)
    )
    paddle = result.first()
    
    if not paddle:
        raise HTTPException(status_code=404, detail="Paddle not found")
    
    # Brand is already loaded via selectinload
    brand = paddle.brand
    
    # Get offers
    offers_result = await session.exec(
        select(MarketOffer)
        .where(MarketOffer.paddle_id == paddle_id, MarketOffer.is_active == True)
        .order_by(MarketOffer.price_brl)
    )
    offers = offers_result.all()
    
    return {
        "id": str(paddle.id),
        "brand": {
            "id": brand.id,
            "name": brand.name,
            "website": brand.website
        } if brand else None,
        "model_name": paddle.model_name,
        "search_keywords": paddle.search_keywords,
        "specs": {
            "core_thickness_mm": paddle.core_thickness_mm,
            "weight_avg_g": paddle.weight_avg_g,
            "face_material": paddle.face_material.value,
            "shape": paddle.shape.value,
        },
        "ratings": {
            "power": paddle.power_rating,
            "control": paddle.control_rating,
            "spin": paddle.spin_rating,
            "sweet_spot": paddle.sweet_spot_rating,
        },
        "ideal_for_tennis_elbow": paddle.ideal_for_tennis_elbow,
        "skill_level": paddle.skill_level.value,
        "market_offers": [
            {
                "store_name": o.store_name,
                "price_brl": float(o.price_brl),
                "url": o.url,
                "last_updated": o.last_updated.isoformat()
            }
            for o in offers
        ]
    }


# ============== Recommendations ==============

@router.post("/recommendations", response_model=RecommendationResult)
@limiter.limit("30/minute")
async def get_recommendations(
    request: Request,
    body: RecommendationRequest,
    session: AsyncSession = Depends(get_session)
):
    """Get personalized paddle recommendations based on user profile."""
    profile = UserProfile(
        skill_level=body.skill_level,
        budget_max_brl=body.budget_max_brl,
        play_style=body.play_style,
        has_tennis_elbow=body.has_tennis_elbow
    )
    
    engine = RecommendationEngine(session)
    return await engine.get_recommendations(profile, limit=body.limit)


# ============== Search ==============

@router.get("/search")
@limiter.limit("60/minute")
async def search_paddles(
    request: Request,
    q: str = Query(min_length=2),
    limit: int = Query(default=10, le=50),
    session: AsyncSession = Depends(get_session)
):
    """Fuzzy search for paddles."""
    result = await session.exec(select(PaddleMaster).options(selectinload(PaddleMaster.brand)))
    all_paddles = result.all()
    
    # Score each paddle
    scored = []
    for paddle in all_paddles:
        # Check model name
        score = fuzz.partial_ratio(q.lower(), paddle.model_name.lower())
        
        # Check brand name
        if paddle.brand:
            brand_score = fuzz.partial_ratio(q.lower(), paddle.brand.name.lower())
            score = max(score, brand_score)
        
        # Check keywords
        for kw in paddle.search_keywords:
            kw_score = fuzz.partial_ratio(q.lower(), kw.lower())
            score = max(score, kw_score)
        
        if score >= 50:  # Threshold
            # Get min price
            price_result = await session.exec(
                select(func.min(MarketOffer.price_brl))
                .where(MarketOffer.paddle_id == paddle.id, MarketOffer.is_active == True)
            )
            min_price = price_result.first()
            
            scored.append({
                "id": str(paddle.id),
                "brand_name": paddle.brand.name if paddle.brand else None,
                "model_name": paddle.model_name,
                "match_score": score,
                "min_price_brl": float(min_price) if min_price else None
            })
    
    # Sort by score and limit
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    
    return {
        "query": q,
        "results": scored[:limit],
        "total": len(scored)
    }
