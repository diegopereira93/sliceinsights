"""
Recommendation API endpoints.
"""
from fastapi import APIRouter, Depends, Request
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from slowapi import Limiter
from slowapi.util import get_remote_address
from uuid import UUID

from app.db.database import get_session
from app.models import PaddleMaster, MarketOffer
from app.schemas.user_profile import (
    RecommendationRequest, RecommendationResult,
    UserProfile, PaddleRecommendation, MarketOfferOut
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.recommendation_engine import RecommendationEngine
from app.services.llm_service import llm_service
from app.services.affiliate_service import get_affiliate_service

router = APIRouter(prefix="/recommend", tags=["recommend"])
limiter = Limiter(key_func=get_remote_address)


@router.post("", response_model=RecommendationResult)
@limiter.limit("30/minute")
async def post_recommendations(
    request: Request,
    body: RecommendationRequest,
    session: AsyncSession = Depends(get_session)
):
    """Get paddle recommendations based on user profile."""
    # Build UserProfile from request body
    profile = UserProfile(
        skill_level=body.skill_level,
        budget_max_brl=body.budget_max_brl,
        play_style=body.play_style,
        has_tennis_elbow=body.has_tennis_elbow,
        spin_preference=body.spin_preference,
        weight_preference=body.weight_preference,
        power_preference_percent=body.power_preference_percent
    )
    
    # Get recommendations from engine
    engine = RecommendationEngine(session)
    result = await engine.get_recommendations(profile, limit=body.limit, use_ai_ranking=True)
    
    # If recommendations exist, enrich with market_offers
    if result.recommendations:
        paddle_ids = [r.paddle_id for r in result.recommendations]
        
        # Query paddles with market_offers and store loaded
        stmt = (
            select(PaddleMaster)
            .options(selectinload(PaddleMaster.market_offers).selectinload(MarketOffer.store))
            .where(PaddleMaster.id.in_(paddle_ids))
        )
        paddles_result = await session.exec(stmt)
        # Handle both tuple and single result formats
        all_results = paddles_result.all()
        paddles_map = {}
        for r in all_results:
            if isinstance(r, tuple):
                paddles_map[r[0].id] = r[0]
            else:
                paddles_map[r.id] = r
        
        # Get affiliate service
        affiliate = get_affiliate_service()
        
        # Enrich each recommendation with market_offers and image_url
        for rec in result.recommendations:
            paddle = paddles_map.get(rec.paddle_id)
            if paddle:
                # Set image_url
                rec.image_url = paddle.image_url
                
                # Build market_offers from active offers, sorted by price
                active_offers = [o for o in paddle.market_offers if o.is_active]
                rec.market_offers = sorted(
                    [
                        MarketOfferOut(
                            store_name=o.store.name,
                            price_brl=float(o.price_brl),
                            store_url=affiliate.transform_url(o.url, store_name=o.store.name),
                        )
                        for o in active_offers
                    ],
                    key=lambda x: x.price_brl,
                )
    
    # If no recommendations, generate a no-match dossier
    if len(result.recommendations) == 0:
        no_match_dossier = await llm_service.generate_dossier(
            user_profile=profile.model_dump(),
            top_paddles=[]
        )
        result.grok_dossier = no_match_dossier
    
    return result


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("60/minute")
async def post_chat(
    request: Request,
    body: ChatRequest
):
    """Chat with the recommendation assistant."""
    # Convert messages to dict format
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    
    # Get response from LLM service
    reply = await llm_service.chat_with_context(
        chat_history=messages,
        context=body.context
    )
    
    return ChatResponse(reply=reply)