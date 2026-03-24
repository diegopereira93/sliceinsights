"""
Orval-compatible shim endpoints for the Vite frontend.
These endpoints serve the exact JSON schemas expected by the redesign-slice API client.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Request
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, EmailStr

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.database import get_session
from app.models import PaddleMaster, MarketOffer, Brand, Lead
from app.models.brand import Brand as BrandModel
from app.services.recommendation_engine import RecommendationEngine
from app.services.llm_service import llm_service
from app.schemas.user_profile import UserProfile

router = APIRouter(prefix="/api", tags=["orval-shim"])
limiter = Limiter(key_func=get_remote_address)


# ============== Helper Functions ==============


def paddle_to_orval(paddle: PaddleMaster, seq_id: int) -> dict:
    """Convert PaddleMaster SQLModel to Orval Paddle dict."""
    # Get active offers - handle both ORM objects and raw rows
    try:
        active_offers = [o for o in paddle.market_offers if o.is_active]
    except AttributeError:
        # For raw SQL rows, try to access market_offers differently
        active_offers = []
        if hasattr(paddle, "_extra"):
            offers = paddle._extra.get("market_offers", [])
            active_offers = [o for o in offers if getattr(o, "is_active", False)]

    # Find minimum price offer
    min_offer = (
        min(active_offers, key=lambda o: o.price_brl, default=None) if active_offers else None
    )

    # Calculate ratings
    power = paddle.power_rating or 5
    control = paddle.control_rating or 5
    rating = round((power + control) / 2, 1)

    # Calculate price
    price = float(min_offer.price_brl) if min_offer else 0.0

    # isHiddenGem: rating >= 7 AND price < 600 AND not featured
    is_gem = rating >= 7 and price > 0 and price < 600 and not paddle.is_featured

    return {
        "id": seq_id,
        "name": paddle.model_name,
        "brand": paddle.brand.name if paddle.brand else "Unknown",
        "price": price,
        "rating": rating,
        "imageUrl": paddle.image_url,
        "coreThickness": float(paddle.core_thickness_mm) if paddle.core_thickness_mm else None,
        "surface": paddle.face_material.value if paddle.face_material else None,
        "handle": None,
        "swingWeight": paddle.swing_weight,
        "powerScore": power,
        "controlScore": control,
        "weightSensation": None,
        "weightSensationDescription": None,
        "shopUrl": min_offer.url if min_offer else None,
        "isHiddenGem": is_gem,
        "valueCostBenefit": None,
    }


def budget_to_max(budget: str) -> float:
    """Convert budget string to max price."""
    mapping = {
        "under300": 300,
        "300to600": 600,
        "600to900": 900,
        "over900": 99999,
    }
    return mapping.get(budget, 99999)


# ============== Request/Response Models ==============


class QuizAnswers(BaseModel):
    skillLevel: str
    playStyle: str
    budget: str
    gripSize: Optional[str] = None
    corePreference: Optional[str] = None
    injuryHistory: Optional[bool] = None
    competitionLevel: str
    primaryShot: Optional[str] = None
    physicalBuild: Optional[str] = None
    previousBrand: Optional[str] = None


class LeadInput(BaseModel):
    name: str
    email: EmailStr
    quizAnswers: Optional[QuizAnswers] = None
    recommendedPaddleId: Optional[int] = None


class LeadResponse(BaseModel):
    success: bool
    message: str


class ChatHistoryItem(BaseModel):
    role: str
    content: str


class ChatMessageInput(BaseModel):
    message: str
    conversationHistory: Optional[List[ChatHistoryItem]] = None
    recommendedPaddleId: Optional[int] = None
    quizAnswers: Optional[QuizAnswers] = None


class ChatMessageResponse(BaseModel):
    reply: str
    suggestedPaddleIds: Optional[List[int]] = None


class IdealSpec(BaseModel):
    coreThickness: Optional[float] = None
    surface: Optional[str] = None
    powerBalance: Optional[float] = None


class PaddleListResponse(BaseModel):
    paddles: List[dict]
    total: int


class QuizRecommendation(BaseModel):
    topPick: dict
    alternatives: List[dict]
    reasoning: str
    idealSpec: Optional[IdealSpec] = None


# ============== Endpoints ==============


@router.get("/healthz")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/paddles", response_model=PaddleListResponse)
@limiter.limit("100/minute")
async def list_paddles(
    request: Request,
    brand: Optional[str] = Query(default=None),
    minPrice: Optional[float] = Query(default=None),
    maxPrice: Optional[float] = Query(default=None),
    coreThickness: Optional[float] = Query(default=None),
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List paddles with filters."""
    # Build offer subquery for min prices
    offer_subq = (
        select(
            MarketOffer.paddle_id,
            func.min(MarketOffer.price_brl).label("min_price"),
        )
        .where(MarketOffer.is_active.is_(True))
        .group_by(MarketOffer.paddle_id)
        .subquery()
    )

    # Base query with row_number for sequential IDs
    base_query = (
        select(
            PaddleMaster,
            func.row_number().over(order_by=PaddleMaster.created_at).label("seq_id"),
            offer_subq.c.min_price,
        )
        .options(
            selectinload(PaddleMaster.brand),
            selectinload(PaddleMaster.market_offers),
        )
        .join(offer_subq, PaddleMaster.id == offer_subq.c.paddle_id)
    )

    # Apply filters
    if brand:
        base_query = base_query.join(BrandModel, PaddleMaster.brand_id == BrandModel.id).where(
            BrandModel.name.ilike(f"%{brand}%")
        )

    if minPrice is not None or maxPrice is not None:
        base_query = base_query.join(offer_subq, PaddleMaster.id == offer_subq.c.paddle_id)
        if minPrice is not None:
            base_query = base_query.where(offer_subq.c.min_price >= minPrice)
        if maxPrice is not None:
            base_query = base_query.where(offer_subq.c.min_price <= maxPrice)

    if coreThickness is not None:
        base_query = base_query.where(PaddleMaster.core_thickness_mm == coreThickness)

    if search:
        base_query = base_query.where(PaddleMaster.model_name.ilike(f"%{search}%"))

    # Get total count
    count_query = select(func.count(PaddleMaster.id)).select_from(
        select(PaddleMaster).join(offer_subq, PaddleMaster.id == offer_subq.c.paddle_id).subquery()
    )
    count_result = await session.exec(count_query)
    total = count_result.first() or 0

    # Get paginated results
    query = base_query.order_by(PaddleMaster.created_at).offset(offset).limit(limit)
    result = await session.exec(query)
    paddles_db = result.scalars().all()

    # Convert to Orval format
    paddles = []
    for idx, paddle in enumerate(paddles_db):
        seq_id = offset + idx + 1
        paddles.append(paddle_to_orval(paddle, seq_id))

    return {"paddles": paddles, "total": total}


@router.get("/paddles/{paddle_id}")
@limiter.limit("100/minute")
async def get_paddle(
    request: Request,
    paddle_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a single paddle by sequential ID."""
    # Query all paddles with row_number to map sequential ID
    offer_subq = (
        select(
            MarketOffer.paddle_id,
            func.min(MarketOffer.price_brl).label("min_price"),
        )
        .where(MarketOffer.is_active.is_(True))
        .group_by(MarketOffer.paddle_id)
        .subquery()
    )

    query = (
        select(
            PaddleMaster,
            func.row_number().over(order_by=PaddleMaster.created_at).label("seq_id"),
        )
        .options(
            selectinload(PaddleMaster.brand),
            selectinload(PaddleMaster.market_offers),
        )
        .join(offer_subq, PaddleMaster.id == offer_subq.c.paddle_id)
    )

    result = await session.exec(query)
    rows = result.all()

    # Find the paddle with matching seq_id
    for row in rows:
        paddle = row[0] if isinstance(row, tuple) else row
        seq_id = row.seq_id if hasattr(row, "seq_id") else 0
        if seq_id == paddle_id:
            return paddle_to_orval(paddle, seq_id)

    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail="Paddle not found")


@router.post("/quiz/recommend", response_model=QuizRecommendation)
@limiter.limit("30/minute")
async def quiz_recommend(
    request: Request,
    body: QuizAnswers,
    session: AsyncSession = Depends(get_session),
):
    """Get paddle recommendations based on quiz answers."""
    # Convert budget to max price
    budget_max = budget_to_max(body.budget)

    # Build user profile
    profile = UserProfile(
        skill_level=body.skillLevel,
        budget_max_brl=budget_max,
        play_style=body.playStyle,
        has_tennis_elbow=body.injuryHistory or False,
        spin_preference="medium",
        weight_preference="medium",
        power_preference_percent=50,
    )

    # Get recommendations from engine
    engine = RecommendationEngine(session)
    result = await engine.get_recommendations(profile, limit=5, use_ai_ranking=True)

    # Build the response
    if result.recommendations:
        # Get paddle details for top pick
        top_paddle_id = result.recommendations[0].paddle_id
        paddle_query = (
            select(PaddleMaster)
            .options(
                selectinload(PaddleMaster.brand),
                selectinload(PaddleMaster.market_offers),
            )
            .where(PaddleMaster.id == top_paddle_id)
        )
        paddle_result = await session.exec(paddle_query)
        top_paddle = paddle_result.first()

        top_pick = paddle_to_orval(top_paddle, 1) if top_paddle else {}

        # Get alternatives
        alternatives = []
        for i, rec in enumerate(result.recommendations[1:4], start=2):
            alt_query = (
                select(PaddleMaster)
                .options(
                    selectinload(PaddleMaster.brand),
                    selectinload(PaddleMaster.market_offers),
                )
                .where(PaddleMaster.id == rec.paddle_id)
            )
            alt_result = await session.exec(alt_query)
            alt_paddle = alt_result.first()
            if alt_paddle:
                alternatives.append(paddle_to_orval(alt_paddle, i))

        # Build reasoning from AI
        reasoning = result.grok_dossier or "Recomendação baseada no seu perfil de jogo."

        # Build ideal spec
        ideal_spec = IdealSpec(
            coreThickness=16
            if body.playStyle == "power"
            else (14 if body.playStyle == "control" else 15),
            surface="Carbon" if body.skillLevel in ["intermediate", "advanced"] else "Fiberglass",
            powerBalance=0.7
            if body.playStyle == "power"
            else (0.3 if body.playStyle == "control" else 0.5),
        )

        return QuizRecommendation(
            topPick=top_pick,
            alternatives=alternatives,
            reasoning=reasoning,
            idealSpec=ideal_spec,
        )

    # No recommendations fallback
    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail="No recommendations found for your profile")


@router.post("/leads", response_model=LeadResponse)
@limiter.limit("30/minute")
async def create_lead(
    request: Request,
    body: LeadInput,
    session: AsyncSession = Depends(get_session),
):
    """Create a new lead."""
    lead = Lead(email=body.email, name=body.name)
    session.add(lead)
    await session.commit()

    return LeadResponse(success=True, message="Lead capturado com sucesso")


@router.post("/chat", response_model=ChatMessageResponse)
@limiter.limit("60/minute")
async def chat_message(
    request: Request,
    body: ChatMessageInput,
):
    """Chat with the recommendation assistant."""
    # Build context from quiz answers if provided
    context_parts = []
    if body.quizAnswers:
        qa = body.quizAnswers
        context_parts.append(f"Usuário: {qa.skillLevel} - {qa.playStyle} - orçamento {qa.budget}")

    # Build messages from conversation history
    messages = []
    if body.conversationHistory:
        for msg in body.conversationHistory:
            messages.append({"role": msg.role, "content": msg.content})

    # Add current message
    messages.append({"role": "user", "content": body.message})

    # Get response from LLM service
    context = (
        " | ".join(context_parts)
        if context_parts
        else "Usuário buscando recomendações de raquetes de Pickleball."
    )
    reply = await llm_service.chat_with_context(chat_history=messages, context=context)

    return ChatMessageResponse(reply=reply, suggestedPaddleIds=None)


@router.get("/stats/market")
@limiter.limit("60/minute")
async def get_market_stats(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Get market statistics."""
    # Query all paddles with offers
    offer_subq = (
        select(
            MarketOffer.paddle_id,
            func.min(MarketOffer.price_brl).label("min_price"),
        )
        .where(MarketOffer.is_active.is_(True))
        .group_by(MarketOffer.paddle_id)
        .subquery()
    )

    brand_subq = select(
        Brand.id,
        Brand.name.label("brand_name"),
    ).subquery()

    query = (
        select(
            brand_subq.c.brand_name,
            PaddleMaster,
            offer_subq.c.min_price,
        )
        .outerjoin(brand_subq, PaddleMaster.brand_id == brand_subq.c.id)
        .join(offer_subq, PaddleMaster.id == offer_subq.c.paddle_id)
    )

    result = await session.exec(query)
    rows = result.all()

    total_paddles = len(rows)

    # Calculate average price
    prices = []
    core_thickness_dist: Dict[str, int] = {}
    surface_dist: Dict[str, int] = {}
    power_vs_control = []
    best_value = None
    top_power = None
    best_value_ratio = 0
    top_power_score = 0

    for row in rows:
        brand_name = row[0]
        paddle = row[1]
        min_price = row[2]

        if min_price:
            prices.append(float(min_price))

        # Core thickness distribution
        if paddle.core_thickness_mm:
            key = f"{int(paddle.core_thickness_mm)}mm"
            core_thickness_dist[key] = core_thickness_dist.get(key, 0) + 1

        # Surface distribution
        if paddle.face_material:
            key = paddle.face_material.value
            surface_dist[key] = surface_dist.get(key, 0) + 1

        # Calculate rating
        power = paddle.power_rating or 5
        control = paddle.control_rating or 5
        rating = (power + control) / 2

        # Best value: highest rating/price ratio
        if min_price and float(min_price) > 0:
            ratio = rating / float(min_price)
            if ratio > best_value_ratio:
                best_value_ratio = ratio
                best_value = {
                    "id": 0,
                    "name": paddle.model_name,
                    "brand": brand_name or "Unknown",
                    "price": float(min_price),
                    "rating": rating,
                    "imageUrl": paddle.image_url,
                    "coreThickness": float(paddle.core_thickness_mm)
                    if paddle.core_thickness_mm
                    else None,
                    "surface": paddle.face_material.value if paddle.face_material else None,
                    "handle": None,
                    "swingWeight": paddle.swing_weight,
                    "powerScore": power,
                    "controlScore": control,
                    "weightSensation": None,
                    "weightSensationDescription": None,
                    "shopUrl": None,
                    "isHiddenGem": rating >= 7
                    and float(min_price) > 0
                    and float(min_price) < 600
                    and not paddle.is_featured,
                    "valueCostBenefit": None,
                }

        # Top power: highest power score
        if power > top_power_score:
            top_power_score = power
            top_power = {
                "id": 0,
                "name": paddle.model_name,
                "brand": brand_name or "Unknown",
                "price": float(min_price) if min_price else 0,
                "rating": rating,
                "imageUrl": paddle.image_url,
                "coreThickness": float(paddle.core_thickness_mm)
                if paddle.core_thickness_mm
                else None,
                "surface": paddle.face_material.value if paddle.face_material else None,
                "handle": None,
                "swingWeight": paddle.swing_weight,
                "powerScore": power,
                "controlScore": control,
                "weightSensation": None,
                "weightSensationDescription": None,
                "shopUrl": None,
                "isHiddenGem": False,
                "valueCostBenefit": None,
            }

        # Power vs control data (limit to 30)
        if len(power_vs_control) < 30:
            power_vs_control.append(
                {
                    "name": paddle.model_name,
                    "brand": brand_name or "Unknown",
                    "power": power,
                    "control": control,
                    "price": float(min_price) if min_price else 0,
                }
            )

    avg_price = sum(prices) / len(prices) if prices else 0

    # Price range distribution
    price_ranges = {"0-300": 0, "300-600": 0, "600-900": 0, "900+": 0}
    for p in prices:
        if p < 300:
            price_ranges["0-300"] += 1
        elif p < 600:
            price_ranges["300-600"] += 1
        elif p < 900:
            price_ranges["600-900"] += 1
        else:
            price_ranges["900+"] += 1

    # Market insight
    most_common_core = (
        max(core_thickness_dist.items(), key=lambda x: x[1]) if core_thickness_dist else ("N/A", 0)
    )
    insight = f"{most_common_core[1]} raquetes têm núcleo de {most_common_core[0]} ({most_common_core[1] * 100 // total_paddles if total_paddles else 0}% do catálogo)"

    return {
        "totalPaddles": total_paddles,
        "averagePrice": round(avg_price, 2),
        "bestValue": best_value,
        "topPower": top_power,
        "coreThicknessDistribution": core_thickness_dist,
        "priceRangeDistribution": price_ranges,
        "surfaceDistribution": surface_dist,
        "powerVsControlData": power_vs_control,
        "marketInsight": insight,
    }


@router.get("/stats/brands")
@limiter.limit("60/minute")
async def get_brand_stats(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Get brand statistics."""
    # Query paddles grouped by brand
    offer_subq = (
        select(
            MarketOffer.paddle_id,
            func.min(MarketOffer.price_brl).label("min_price"),
        )
        .where(MarketOffer.is_active.is_(True))
        .group_by(MarketOffer.paddle_id)
        .subquery()
    )

    brand_subq = select(
        Brand.id,
        Brand.name.label("brand_name"),
    ).subquery()

    query = (
        select(
            brand_subq.c.brand_name,
            PaddleMaster,
            offer_subq.c.min_price,
        )
        .outerjoin(brand_subq, PaddleMaster.brand_id == brand_subq.c.id)
        .join(offer_subq, PaddleMaster.id == offer_subq.c.paddle_id)
    )

    result = await session.exec(query)
    rows = result.all()

    # Group by brand
    brand_data: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        brand_name = row[0]
        paddle = row[1]
        min_price = row[2]

        if not brand_name:
            continue

        if brand_name not in brand_data:
            brand_data[brand_name] = {
                "count": 0,
                "total_price": 0,
                "total_rating": 0,
            }

        brand_data[brand_name]["count"] += 1

        if min_price:
            brand_data[brand_name]["total_price"] += float(min_price)

        power = paddle.power_rating or 5
        control = paddle.control_rating or 5
        rating = (power + control) / 2
        brand_data[brand_name]["total_rating"] += rating

    # Calculate total for market share
    total_paddles = sum(b["count"] for b in brand_data.values())

    # Build response
    stats = []
    for brand_name, data in brand_data.items():
        avg_price = data["total_price"] / data["count"] if data["count"] else 0
        avg_rating = data["total_rating"] / data["count"] if data["count"] else 0
        market_share = (data["count"] / total_paddles * 100) if total_paddles else 0

        stats.append(
            {
                "brand": brand_name,
                "count": data["count"],
                "avgPrice": round(avg_price, 2),
                "avgRating": round(avg_rating, 1),
                "marketShare": round(market_share, 1),
            }
        )

    # Sort by count descending
    stats.sort(key=lambda x: x["count"], reverse=True)

    return stats


@router.get("/stats/hidden-gems")
@limiter.limit("60/minute")
async def get_hidden_gems(
    request: Request,
    limit: int = Query(default=10, le=20, ge=1),
    session: AsyncSession = Depends(get_session),
):
    """Get hidden gems - high rating, low price, not featured."""
    offer_subq = (
        select(
            MarketOffer.paddle_id,
            func.min(MarketOffer.price_brl).label("min_price"),
        )
        .where(MarketOffer.is_active.is_(True))
        .group_by(MarketOffer.paddle_id)
        .subquery()
    )

    query = (
        select(
            PaddleMaster,
            offer_subq.c.min_price,
        )
        .options(
            selectinload(PaddleMaster.brand),
            selectinload(PaddleMaster.market_offers),
        )
        .join(offer_subq, PaddleMaster.id == offer_subq.c.paddle_id)
    )

    result = await session.exec(query)
    rows = result.all()

    # Filter hidden gems: rating >= 7, price < 600, not featured
    gems = []
    for i, row in enumerate(rows):
        paddle = row[0] if isinstance(row, tuple) else row
        min_price = row[1] if isinstance(row, tuple) else None

        if not min_price:
            continue

        power = paddle.power_rating or 5
        control = paddle.control_rating or 5
        rating = (power + control) / 2

        price = float(min_price)
        is_gem = rating >= 7 and price > 0 and price < 600 and not paddle.is_featured

        if is_gem:
            gems.append(paddle_to_orval(paddle, len(gems) + 1))
            if len(gems) >= limit:
                break

    return gems
