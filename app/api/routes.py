"""
FastAPI routes for PickleMatch Advisor API.
"""
from typing import Optional
from uuid import UUID

from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
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
from app.models.lead import Lead, LeadCreate, LeadRead
from app.schemas.user_profile import RecommendationRequest, RecommendationResult, UserProfile
from app.services.recommendation_engine import RecommendationEngine
from app.services.affiliate_service import get_affiliate_service
from app.api.endpoints.history import router as history_router
from app.services.llm_service import llm_service
from app.schemas.chat import ChatRequest, ChatResponse

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
        # Use a short timeout for the health check to avoid hanging
        await session.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        import structlog
        logger = structlog.get_logger()
        logger.error("Health check failed", error=str(e))
        # Don't fail the whole app if DB is just warming up, but return 503
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "version": "1.0.0",
                "database": "disconnected",
                "detail": str(e)
            }
        )


# ============== Admin (Seed Trigger) ==============

@router.get("/admin/diag")
async def diagnostics(
    secret: str = Query(..., description="Admin secret key"),
):
    """
    Diagnostic endpoint to check database and file configuration.
    """
    import os
    from pathlib import Path
    
    admin_secret = os.getenv("ADMIN_SEED_SECRET", "sliceinsights2026")
    if secret != admin_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Check data files - now in app/data/ for container compatibility
    app_dir = Path(__file__).parent.parent  # /app/app
    data_dir = app_dir / "data"
    
    data_files = {
        "paddle_stats_dump.csv": (data_dir / "paddle_stats_dump.csv").exists(),
        "brazil_pickleball_store.csv": (data_dir / "brazil_pickleball_store.csv").exists(),
        "joola_brazil.csv": (data_dir / "joola_brazil.csv").exists(),
    }
    
    # List what actually exists
    try:
        data_dir_contents = list(data_dir.iterdir()) if data_dir.exists() else []
    except Exception as e:
        data_dir_contents = [f"Error: {str(e)}"]
    
    # Check environment variables (masked)
    db_url = os.getenv("DATABASE_URL", "NOT SET")
    db_url_sync = os.getenv("DATABASE_URL_SYNC", "NOT SET")
    seed_force = os.getenv("SEED_FORCE_CLEAR", "NOT SET")
    
    return {
        "data_files": data_files,
        "all_files_exist": all(data_files.values()),
        "data_dir_exists": data_dir.exists(),
        "data_dir_contents": [str(p.name) for p in data_dir_contents] if isinstance(data_dir_contents, list) else data_dir_contents,
        "env": {
            "DATABASE_URL": f"{db_url[:30]}..." if len(db_url) > 30 else db_url,
            "DATABASE_URL_SYNC": f"{db_url_sync[:30]}..." if len(db_url_sync) > 30 else db_url_sync,
            "SEED_FORCE_CLEAR": seed_force,
        },
        "app_dir": str(app_dir),
    }


@router.post("/admin/seed")
async def trigger_seed(
    secret: str = Query(..., description="Admin secret key"),
):
    """
    Trigger database seed manually (SYNCHRONOUS).
    Protected by secret key to prevent abuse.
    """
    import os
    admin_secret = os.getenv("ADMIN_SEED_SECRET", "sliceinsights2026")
    
    if secret != admin_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    try:
        os.environ["SEED_FORCE_CLEAR"] = "true"
        
        # Import and run synchronously for better error handling
        from app.db.seed_data_hybrid import seed_database_hybrid
        seed_database_hybrid()
        
        # Count results
        from sqlmodel import select
        from app.db.database import sync_engine
        from sqlmodel import Session
        
        with Session(sync_engine) as session:
            brands_count = len(session.exec(select(Brand)).all())
            paddles_count = len(session.exec(select(PaddleMaster)).all())
        
        return {
            "status": "seed_completed",
            "brands_created": brands_count,
            "paddles_created": paddles_count,
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Seed failed: {str(e)}\n\nTraceback:\n{traceback.format_exc()}")


# ============== Brands ==============

@router.get("/brands", response_model=dict)
async def list_brands(
    available_in_brazil: Optional[bool] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """List all brands (cached for 5 minutes)."""
    # Cache key includes filter now
    cache_key = f"all_brands_{available_in_brazil}"
    
    # Check cache first
    if cache_key in _brands_cache:
        return _brands_cache[cache_key]
    
    query = select(Brand)
    
    if available_in_brazil is not None:
        # Join with PaddleMaster and filter, ensure distinct brands
        query = (
            query
            .join(PaddleMaster, Brand.id == PaddleMaster.brand_id)
            .where(PaddleMaster.available_in_brazil == available_in_brazil)
            .distinct()
        )
    
    result = await session.exec(query)
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
    available_in_brazil: Optional[bool] = Query(
        default=None,
        description="Filter by Brazilian market availability (True for BR only, False for International only, None for all)"
    ),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = Query(default=50, le=100),  # Aumentado para 50 para mostrar catálogo BR completo
    offset: int = 0,
    session: AsyncSession = Depends(get_session)
):
    """List paddles with optional filters. Optimized to avoid N+1 queries."""
    
    # Create subquery for market offer aggregations
    offer_subq = (
        select(
            MarketOffer.paddle_id,
            func.min(MarketOffer.price_brl).label("min_price"),
            func.count(MarketOffer.id).label("offer_count")
        )
        .where(MarketOffer.is_active.is_(True)) # noqa: E712
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
    if available_in_brazil is not None:
        query = query.where(PaddleMaster.available_in_brazil == available_in_brazil)
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
    if available_in_brazil is not None:
        count_query = count_query.where(PaddleMaster.available_in_brazil == available_in_brazil)
    
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
    """Get paddle details with market offers (affiliate URLs applied)."""
    result = await session.exec(
        select(PaddleMaster)
        .options(selectinload(PaddleMaster.brand))
        .where(PaddleMaster.id == paddle_id)
    )
    paddle = result.first()
    
    if not paddle:
        raise HTTPException(status_code=404, detail="Paddle not found")
    
    # Get offers
    offers_result = await session.exec(
        select(MarketOffer)
        .where(MarketOffer.paddle_id == paddle_id, MarketOffer.is_active.is_(True)) # noqa: E712
        .order_by(MarketOffer.price_brl)
    )
    offers = offers_result.all()
    min_price = float(offers[0].price_brl) if offers else None
    
    # Apply affiliate transformations
    affiliate_service = get_affiliate_service()
    
    # Use the consolidated schema logic
    paddle_read = PaddleRead.from_paddle(paddle, min_price=min_price, offers_count=len(offers))
    
    return {
        "id": str(paddle_read.id),
        "brand": {
            "id": paddle_read.brand_id,
            "name": paddle_read.brand_name
        },
        "model_name": paddle_read.model_name,
        "available_in_brazil": paddle_read.available_in_brazil,
        "specs": paddle_read.specs.model_dump(),
        "ratings": paddle_read.ratings.model_dump(),
        "market_offers": [
            {
                "store_name": o.store_name,
                "price_brl": float(o.price_brl),
                "url": affiliate_service.transform_url(o.url, o.store_name),
                "affiliate_url": affiliate_service.transform_url(o.url, o.store_name) if affiliate_service.is_affiliate_enabled() else None,
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
    result = await engine.get_recommendations(profile, limit=body.limit)
    
    # Generate the personalized AI dossier from the Groq LLM
    try:
        if result.recommendations:
            # Fetch full paddle objects for specs context
            paddle_ids = [rec.paddle_id for rec in result.recommendations]
            paddles_result = await session.exec(
                select(PaddleMaster).where(PaddleMaster.id.in_(paddle_ids))
            )
            paddles_by_id = {p.id: p for p in paddles_result.all()}
            
            # Build RICH context with all structured data (SCI)
            # Build RICH context with all structured data (SCI)
            # Remove internal flags and raw Enum names to prevent LLM hallucination/robotic speaking
            paddles_context = []
            for rec in result.recommendations:
                paddle = paddles_by_id.get(rec.paddle_id)
                entry = {
                    "Marca": rec.brand_name,
                    "Modelo": rec.model_name,
                    "Custo-Benefício": "Excepcional" if rec.value_score and rec.value_score > 10 else ("Bom" if rec.value_score and rec.value_score > 7 else "Regular"),
                    "Preço": f"R$ {rec.min_price_brl:.2f}" if rec.min_price_brl else "Sob consulta",
                    "Motivos para Escolher": rec.match_reasons,
                }
                if paddle:
                    # Clean Enum formatting
                    face_mat = paddle.face_material.value if hasattr(paddle.face_material, "value") else str(paddle.face_material) if paddle.face_material else "Não informado"
                    shape_val = paddle.shape.value if hasattr(paddle.shape, "value") else str(paddle.shape) if paddle.shape else "Não informada"
                    
                    entry["Especificações Físicas"] = {
                        "Espessura do núcleo (mm)": paddle.core_thickness_mm or "Não informado",
                        "Material do núcleo": paddle.core_material or "Não informado",
                        "Material da face": face_mat.title() if face_mat != "Não informado" else face_mat,
                        "Formato": shape_val.title() if shape_val != "Não informada" else shape_val,
                    }
                    
                    # Add numeric ratings ONLY if specs_confidence is HIGH
                    # We pass the internal float to LLM but disguise the key so the LLM acts naturally
                    entry["specs_confidence"] = paddle.specs_confidence
                    if paddle.specs_confidence >= 0.75:
                        entry["Notas de Performance"] = {
                            "Potência (Power)": rec.ratings.get("power", "N/A"),
                            "Controle (Control)": rec.ratings.get("control", "N/A"),
                            "Spin (Efeito)": rec.ratings.get("spin", "N/A"),
                            "Sweet Spot (Área de acerto)": rec.ratings.get("sweet_spot", "N/A"),
                            "Peso de Swing (Swing Weight)": paddle.swing_weight or "N/A",
                            "Peso de Torção (Twist Weight)": paddle.twist_weight or "N/A"
                        }
                        
                paddles_context.append(entry)
            
            # Decode UserProfile into human-readable Portuguese for the LLM
            profile_context = {
                "Nível": profile.skill_level.value,
                "Estilo_de_Jogo": profile.play_style.value,
                "Orçamento": f"até R$ {profile.budget_max_brl:.0f}" if profile.budget_max_brl else "Sem limite",
                "Epicondilite": "Sim" if profile.has_tennis_elbow else "Não",
                "Preferência_Spin": profile.spin_preference or "Sem preferência",
                "Preferência_Peso": profile.weight_preference or "Sem preferência",
                "Slider_Power_vs_Control": f"{profile.power_preference_percent}% Power / {100 - profile.power_preference_percent}% Control" if profile.power_preference_percent is not None else "Não informado",
            }
            
            dossier = await llm_service.generate_dossier(
                user_profile=profile_context,
                top_paddles=paddles_context
            )
            result.grok_dossier = dossier
    except Exception as e:
        import structlog
        structlog.get_logger(__name__).error("Dossier generation failed", error=str(e))
        result.grok_dossier = "Seu perfil foi analisado com sucesso por nossas métricas avançadas."
        
    return result


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
                .where(MarketOffer.paddle_id == paddle.id, MarketOffer.is_active.is_(True)) # noqa: E712
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

# ============== LLM Coach Chat ==============

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def coach_chat(
    request: Request,
    body: ChatRequest,
    session: AsyncSession = Depends(get_session)
):
    """Chat with the AI Coach restricted to the contextual recommendations."""
    # Convert chat history to list of dicts for LLM Service
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    
    reply = await llm_service.chat_with_context(
        chat_history=messages,
        context=body.context
    )
    
    return ChatResponse(reply=reply)

# ============== Leads ==============

@router.post("/leads", response_model=LeadRead, status_code=201)
@limiter.limit("10/minute")
async def create_lead(
    request: Request,
    lead_in: LeadCreate,
    session: AsyncSession = Depends(get_session)
):
    """Capture a new lead email from the Quiz Gate."""
    # Check if exists
    result = await session.exec(select(Lead).where(Lead.email == lead_in.email))
    existing = result.first()
    
    if existing:
        return existing
        
    db_lead = Lead.model_validate(lead_in)
    session.add(db_lead)
    await session.commit()
    await session.refresh(db_lead)
    
    return db_lead

# Include child routers
router.include_router(history_router, prefix="/paddles", tags=["paddles"])
