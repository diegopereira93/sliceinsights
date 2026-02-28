from typing import Optional, List, Dict, Any
from decimal import Decimal
import structlog

from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import PaddleMaster, MarketOffer, Brand
from app.models.paddle import calculate_paddle_ratings
from app.models.enums import PlayStyle
from app.schemas.user_profile import UserProfile, RecommendationResult, PaddleRecommendation
import json
import hashlib
from app.services.llm_service import llm_service

logger = structlog.get_logger(__name__)

class RecommendationEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._cache = {}

    async def get_recommendations(
        self,
        profile: UserProfile,
        limit: int = 3,
        use_ai_ranking: bool = True
    ) -> RecommendationResult:
        """
        Generate paddle recommendations based on user profile with optional AI ranking.
        """
        # 0. Cache Check
        cache_key = self._get_cache_key(profile, limit)
        if cache_key in self._cache:
             return self._cache[cache_key]

        # 1. Subquery for active market offers
        offers_subquery = (
            select(
                MarketOffer.paddle_id,
                func.min(MarketOffer.price_brl).label("min_price"),
                func.count(MarketOffer.id).label("offers_count")
            )
            .where(MarketOffer.is_active.is_(True)) # noqa: E712
            .group_by(MarketOffer.paddle_id)
            .subquery()
        )

        # 2. Base query - Get a larger pool for the AI to choose from
        candidate_pool_limit = 20 if use_ai_ranking else limit
        query = (
            select(
                PaddleMaster,
                Brand.name.label("brand_name"),
                offers_subquery.c.min_price,
                offers_subquery.c.offers_count
            )
            .join(Brand, PaddleMaster.brand_id == Brand.id)
            .outerjoin(offers_subquery, PaddleMaster.id == offers_subquery.c.paddle_id)
            .where(PaddleMaster.specs_confidence >= 0.0)
        )
        
        # 3. Apply Hard Filters
        if profile.has_tennis_elbow:
            # STRICT HARD FILTER: If user has elbow issues, ONLY 16mm+ or those with "Touch/Soft/16mm" markers
            # We must be strict here because the simulation detected 13mm leaks.
            query = query.where(
                (PaddleMaster.core_thickness_mm >= 16.0) | 
                (PaddleMaster.model_name.ilike("%16mm%")) |
                (PaddleMaster.model_name.ilike("%touch%"))
            )
        
        # 4. Diversity Jitter (SCI) - Avoid "3Rdshot Monastery"
        # Since we only send a small pool to the LLM, randomize it so different brands get a chance.
        query = query.order_by(func.random())
        
        if profile.budget_max_brl:
            query = query.where(offers_subquery.c.min_price <= Decimal(str(profile.budget_max_brl)))
        
        # 4. Execute
        result = await self.session.exec(query)
        rows = result.all()
        
        # 4.5 Fallback: If literal filters are too strict, relax budget to find at least 3
        if len(rows) < 3 and profile.budget_max_brl:
            logger.warning("Fewer than 3 paddles found. Relaxing budget filter to fulfill the 3-suggestion rule.")
            # Re-run query without budget limit but keeping medical safety
            query_relaxed = (
                select(
                    PaddleMaster,
                    Brand.name.label("brand_name"),
                    offers_subquery.c.min_price,
                    offers_subquery.c.offers_count
                )
                .join(Brand, PaddleMaster.brand_id == Brand.id)
                .outerjoin(offers_subquery, PaddleMaster.id == offers_subquery.c.paddle_id)
                .where(PaddleMaster.specs_confidence >= 0.0)
            )
            if profile.has_tennis_elbow:
                query_relaxed = query_relaxed.where(
                    (PaddleMaster.core_thickness_mm >= 16.0) | 
                    (PaddleMaster.model_name.ilike("%16mm%")) |
                    (PaddleMaster.model_name.ilike("%touch%"))
                )
            query_relaxed = query_relaxed.order_by(func.random()).limit(10)
            result = await self.session.exec(query_relaxed)
            rows = result.all()
        
        # 5. Ranking Process
        paddles_data = []
        for paddle, brand_name, min_price, offers_count in rows:
            ratings = self._get_paddle_ratings(paddle)
            paddles_data.append({
                "id": str(paddle.id),
                "paddle": paddle,
                "brand_name": brand_name,
                "min_price": float(min_price) if min_price else None,
                "offers_count": offers_count or 0,
                "ratings": ratings,
                "model_name": paddle.model_name
            })
            
        grok_dossier = None
        
        if use_ai_ranking and paddles_data:
            # Shift core intelligence to LLM
            # Prepare a simplified list for the LLM to process
            ai_candidates = [
                {
                    "id": p["id"],
                    "brand": p["brand_name"],
                    "model": p["model_name"],
                    "price": p["min_price"],
                    "ratings": p["ratings"],
                    "confidence": p["paddle"].specs_confidence
                } for p in paddles_data[:candidate_pool_limit]
            ]
            
            ai_result = await llm_service.generate_ai_recommendations(profile.model_dump(), ai_candidates)
            
            # Map LLM results back to objects
            ranked_ids = ai_result.get("ranked_ids", [])
            grok_dossier = ai_result.get("dossier")
            
            # Create a lookup map
            paddles_map = {p["id"]: p for p in paddles_data}
            ranked_paddles = [paddles_map[pid] for pid in ranked_ids if pid in paddles_map]
            
            # Fallback if AI fails or returns weird IDs
            if not ranked_paddles:
                ranked_paddles = self._rank_by_style(paddles_data, profile)[:limit]
        else:
            ranked_paddles = self._rank_by_style(paddles_data, profile)[:limit]
        
        # 6. Build final recommendations
        recommendations = []
        for rank, data in enumerate(ranked_paddles[:3], 1): # Strictly enforce top 3
            paddle = data["paddle"]
            ratings = data["ratings"]
            
            recommendations.append(PaddleRecommendation(
                rank=rank,
                paddle_id=paddle.id,
                brand_name=data["brand_name"],
                model_name=paddle.model_name,
                ratings=ratings,
                min_price_brl=data["min_price"],
                match_reasons=self._get_match_reasons(paddle, ratings, profile),
                tags=self._get_tags(paddle, ratings, profile, rank),
                value_score=self._calculate_value_score(data, profile)
            ))

        result_obj = RecommendationResult(
            user_profile=profile,
            recommendations=recommendations,
            grok_dossier=grok_dossier,
            filters_applied={
                "budget_filter": profile.budget_max_brl is not None,
                "tennis_elbow_filter": profile.has_tennis_elbow,
            },
            total_matching=len(rows),
            returned=len(recommendations),
        )
        
        self._cache[cache_key] = result_obj
        return result_obj

    def _get_paddle_ratings(self, paddle: PaddleMaster) -> dict:
        """Unified rating calculation (0-10 scale)."""
        return calculate_paddle_ratings(paddle)

    def _get_cache_key(self, profile: UserProfile, limit: int) -> str:
        """Generate a unique hash for the profile and limit."""
        profile_dict = profile.model_dump()
        profile_json = json.dumps(profile_dict, sort_keys=True, default=str)
        return hashlib.md5(f"{profile_json}:{limit}".encode()).hexdigest()

    def _rank_by_style(
        self,
        paddles_data: list[dict],
        profile: UserProfile
    ) -> list[dict]:
        """Sort paddles based on style preference using unified ratings."""
        
        def score_fn(item):
            ratings = item["ratings"]
            paddle = item["paddle"]
            
            # Base Ratings (scaled 0-10)
            p_val = ratings["power"]
            c_val = ratings["control"]
            
            # TITLE-BASED INFERENCE (SCI) - If data is missing, use keywords
            lower_name = paddle.model_name.lower()
            if p_val is None:
                p_val = 5.0
                if any(x in lower_name for x in ["power", "pro", "3s", "14mm", "attack", "speed"]):
                    p_val += 1.5
            
            if c_val is None:
                c_val = 5.0
                if any(x in lower_name for x in ["control", "16mm", "touch", "soft", "precision"]):
                    c_val += 1.5
            
            # 1. Main Style Score (Primary Sort)
            if profile.power_preference_percent is not None:
                power_weight = profile.power_preference_percent / 100.0
                control_weight = 1.0 - power_weight
                main_score = (p_val * power_weight) + (c_val * control_weight)
            else:
                style = profile.play_style
                if style == PlayStyle.POWER:
                    main_score = p_val * 0.8 + c_val * 0.2
                elif style == PlayStyle.CONTROL:
                    main_score = c_val * 0.8 + p_val * 0.2
                else:  # BALANCED
                    main_score = (p_val + c_val) / 2

            # 2. Tie-Breaker Logic
            confidence = paddle.specs_confidence or 0.0
            price = float(item["min_price"]) if item["min_price"] else 9999.0
            jitter = (hash(paddle.model_name) % 100) / 1000.0

            return (main_score, confidence, -price, jitter)

        return sorted(paddles_data, key=score_fn, reverse=True)

    def _normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize a value to 0-10 scale based on a range."""
        if value is None or max_val == min_val:
            return 0.0
        normalized = (value - min_val) / (max_val - min_val) * 10
        return min(max(normalized, 0), 10)

    def _calculate_value_score(self, data: dict, profile: UserProfile) -> Optional[float]:
        """Calculate score based on specs vs price."""
        if not data.get("min_price") or data["min_price"] < 100:
            return None
            
        price = float(data["min_price"])
        ratings = data["ratings"]
        
        # Only compute value_score from non-None ratings
        real_ratings = [v for v in [ratings["power"], ratings["control"], ratings["spin"]] if v is not None]
        if not real_ratings:
            return None
        
        performance = sum(real_ratings) / len(real_ratings)
        
        # Formula: (Performance / Price) * 1000
        value_score = (performance / price) * 1000
        return round(value_score, 1)
    
    def _get_match_reasons(
        self,
        paddle: PaddleMaster,
        ratings: dict,
        profile: UserProfile
    ) -> list[str]:
        """Generate match reasons using unified ratings."""
        reasons = []
        
        if profile.play_style == PlayStyle.POWER and ratings["power"] is not None and ratings["power"] >= 8:
            reasons.append(f"Excepcional potência ({ratings['power']}/10)")
        elif profile.play_style == PlayStyle.CONTROL and ratings["control"] is not None and ratings["control"] >= 8:
            reasons.append(f"Máxima estabilidade e controle ({ratings['control']}/10)")
        elif profile.play_style == PlayStyle.BALANCED and ratings["power"] is not None and ratings["control"] is not None:
            avg = (ratings["power"] + ratings["control"]) / 2
            if avg >= 7.5:
                reasons.append(f"Equilíbrio ideal entre ataque e defesa (Média {avg:.1f})")
        
        if profile.has_tennis_elbow and paddle.core_thickness_mm and paddle.core_thickness_mm >= 16:
            reasons.append("Núcleo de 16mm para absorção de vibração")
        
        # New: Generic reason if based on market presence
        if not reasons:
             reasons.append("Equipamento com alta demanda no mercado brasileiro")
             if paddle.available_in_brazil:
                 reasons.append("Produto com entrega rápida no Brasil")
            
        return reasons[:3]  # Limit to 3 reasons
    
    def _get_tags(
        self,
        paddle: PaddleMaster,
        ratings: dict,
        profile: UserProfile,
        rank: int
    ) -> list[str]:
        """Generate tags using unified ratings."""
        tags = []
        
        if rank == 1:
            tags.append("Top Pick")
        
        if ratings["power"] is not None and ratings["power"] >= 9:
            tags.append("Power Pro")
        elif ratings["control"] is not None and ratings["control"] >= 9:
            tags.append("Elite Control")
            
        if ratings["spin"] is not None and ratings["spin"] >= 8.5:
            tags.append("Spin Machine")
            
        return tags
