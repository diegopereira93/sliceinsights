from typing import Optional
from decimal import Decimal

from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import PaddleMaster, MarketOffer, Brand
from app.models.paddle import calculate_paddle_ratings
from app.models.enums import PlayStyle
from app.schemas.user_profile import UserProfile, RecommendationResult, PaddleRecommendation
import json
import hashlib
class RecommendationEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        # Simple in-memory cache for this session or shared if needed
        # For now, let's use a class-level or instance-level dictionary-based cache
        # with a basic TTL/Size limit logic if this were a production Redis system.
        # Here we'll use a simple dict for demonstration as per roadmap.
        self._cache = {}

    async def get_recommendations(
        self,
        profile: UserProfile,
        limit: int = 3
    ) -> RecommendationResult:
        """
        Generate paddle recommendations based on user profile with caching.
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
            .where(MarketOffer.is_active == True)
            .group_by(MarketOffer.paddle_id)
            .subquery()
        )

        # 2. Base query
        query = (
            select(
                PaddleMaster,
                Brand.name.label("brand_name"),
                offers_subquery.c.min_price,
                offers_subquery.c.offers_count
            )
            .join(Brand, PaddleMaster.brand_id == Brand.id)
            .outerjoin(offers_subquery, PaddleMaster.id == offers_subquery.c.paddle_id)
        )
        
        # 3. Apply Hard Filters
        if profile.has_tennis_elbow:
            query = query.where(PaddleMaster.core_thickness_mm >= 16.0)
        
        if profile.budget_max_brl:
            query = query.where(offers_subquery.c.min_price <= Decimal(str(profile.budget_max_brl)))
        
        # Weight preference filters disabled - swing_weight data not available yet
        # TODO: Re-enable when swing_weight data is populated
        # if profile.weight_preference == 'heavy':
        #     query = query.where(PaddleMaster.swing_weight >= 120)
        # elif profile.weight_preference == 'light':
        #     query = query.where(PaddleMaster.swing_weight <= 110)
        # elif profile.weight_preference == 'standard':
        #     query = query.where(PaddleMaster.swing_weight.between(110, 120))
        
        # 4. Execute
        result = await self.session.exec(query)
        rows = result.all()
        
        # 5. Ranking
        paddles_data = []
        for paddle, brand_name, min_price, offers_count in rows:
            # Unified rating calculation
            ratings = self._get_paddle_ratings(paddle)
            
            paddles_data.append({
                "paddle": paddle,
                "brand_name": brand_name,
                "min_price": min_price,
                "offers_count": offers_count or 0,
                "ratings": ratings
            })
            
        ranked_paddles = self._rank_by_style(paddles_data, profile)
        
        # 6. Build recommendations
        recommendations = []
        for rank, data in enumerate(ranked_paddles[:limit], 1):
            paddle = data["paddle"]
            ratings = data["ratings"]
            
            recommendations.append(PaddleRecommendation(
                rank=rank,
                paddle_id=paddle.id,
                brand_name=data["brand_name"],
                model_name=paddle.model_name,
                ratings=ratings,
                min_price_brl=float(data["min_price"]) if data["min_price"] else None,
                match_reasons=self._get_match_reasons(paddle, ratings, profile),
                tags=self._get_tags(paddle, ratings, profile, rank),
                value_score=self._calculate_value_score(data, profile)
            ))
        
        result_obj = RecommendationResult(
            user_profile=profile,
            recommendations=recommendations,
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
            norm_power = ratings["power"]
            norm_control = ratings["control"]
            
            # CASE A: Fine-grained Slider Preference (0-100%)
            if profile.power_preference_percent is not None:
                power_weight = profile.power_preference_percent / 100.0
                control_weight = 1.0 - power_weight
                return (norm_power * power_weight) + (norm_control * control_weight)

            # CASE B: Legacy Enum Style
            style = profile.play_style
            if style == PlayStyle.POWER:
                return norm_power * 0.8 + norm_control * 0.2
            elif style == PlayStyle.CONTROL:
                return norm_control * 0.8 + norm_power * 0.2
            else:  # BALANCED
                return (norm_power + norm_control) / 2

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
        
        # Performance aggregate
        performance = (ratings["power"] + ratings["control"] + ratings["spin"]) / 3
        
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
        
        if profile.play_style == PlayStyle.POWER and ratings["power"] >= 8:
            reasons.append(f"Excepcional potência ({ratings['power']}/10)")
        elif profile.play_style == PlayStyle.CONTROL and ratings["control"] >= 8:
            reasons.append(f"Máxima estabilidade e controle ({ratings['control']}/10)")
        elif profile.play_style == PlayStyle.BALANCED:
            avg = (ratings["power"] + ratings["control"]) / 2
            if avg >= 7.5:
                reasons.append(f"Equilíbrio ideal entre ataque e defesa (Média {avg:.1f})")
        
        if profile.has_tennis_elbow and paddle.core_thickness_mm and paddle.core_thickness_mm >= 16:
            reasons.append("Núcleo de 16mm para absorção de vibração")
            
        return reasons
    
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
        
        if ratings["power"] >= 9:
            tags.append("Power Pro")
        elif ratings["control"] >= 9:
            tags.append("Elite Control")
            
        if ratings["spin"] >= 8.5:
            tags.append("Spin Machine")
            
        return tags
