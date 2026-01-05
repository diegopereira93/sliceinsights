from typing import Optional
from decimal import Decimal
from uuid import UUID
from datetime import datetime, timezone

from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
import math

from app.models import PaddleMaster, MarketOffer, Brand
from app.models.enums import PlayStyle, SkillLevel
from app.schemas.user_profile import UserProfile, RecommendationResult, PaddleRecommendation
from functools import lru_cache
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
             # Basic TTL could be added here
             return self._cache[cache_key]

        # 1. Subquery for active market offers (min price and count)
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

        # 2. Base query with joins
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
        
        # 3. Apply Hard Filters at DB level
        if profile.has_tennis_elbow:
            query = query.where(
                PaddleMaster.core_thickness_mm >= 16.0
            )
        
        if profile.budget_max_brl:
            query = query.where(offers_subquery.c.min_price <= Decimal(str(profile.budget_max_brl)))
        
        # Spin preference filter
        if profile.spin_preference == 'high':
            query = query.where(PaddleMaster.spin_rating >= 8)
        elif profile.spin_preference == 'medium':
            query = query.where(PaddleMaster.spin_rating >= 5)
        # 'low' = no filter needed
        
        # Weight preference filter (Using Swing Weight as proxy since weight_g is missing)
        # Light < 110, Standard 110-120, Heavy > 120
        if profile.weight_preference == 'heavy':
            query = query.where(PaddleMaster.swing_weight >= 120)
        elif profile.weight_preference == 'light':
            query = query.where(PaddleMaster.swing_weight <= 110)
        elif profile.weight_preference == 'standard':
            query = query.where(PaddleMaster.swing_weight.between(110, 120))
        
        # 4. Execute single optimized query
        result = await self.session.exec(query)
        rows = result.all()
        
        # 5. Ranking in Python (Soft Filters)
        # Convert rows to a list of dicts for easier ranking
        paddles_data = []
        for paddle, brand_name, min_price, offers_count in rows:
            paddles_data.append({
                "paddle": paddle,
                "brand_name": brand_name,
                "min_price": min_price,
                "offers_count": offers_count or 0
            })
            
        ranked_paddles = self._rank_by_style(paddles_data, profile)
        
        # 6. Build recommendations
        recommendations = []
        for rank, data in enumerate(ranked_paddles[:limit], 1):
            paddle = data["paddle"]
            recommendations.append(PaddleRecommendation(
                rank=rank,
                paddle_id=paddle.id,
                brand_name=data["brand_name"],
                model_name=paddle.model_name,
                ratings={
                    "power": paddle.power_rating,
                    "control": int((paddle.twist_weight or 0) * 1.5), # Synthesized
                    "spin": paddle.spin_rating,
                    "sweet_spot": int((paddle.twist_weight or 0) * 1.4), # Synthesized
                },
                min_price_brl=float(data["min_price"]) if data["min_price"] else None,
                match_reasons=self._get_match_reasons(paddle, profile),
                tags=self._get_tags(paddle, profile, rank),
                value_score=self._calculate_value_score(data, rank, profile)
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
        
        # 7. Store in Cache
        self._cache[cache_key] = result_obj
        return result_obj

    def _get_cache_key(self, profile: UserProfile, limit: int) -> str:
        """Generate a unique hash for the profile and limit."""
        profile_dict = profile.model_dump()
        # Sort keys to ensure consistent hashing
        profile_json = json.dumps(profile_dict, sort_keys=True, default=str)
        return hashlib.md5(f"{profile_json}:{limit}".encode()).hexdigest()

    def _rank_by_style(
        self,
        paddles_data: list[dict],
        profile: UserProfile
    ) -> list[dict]:
        """Sort paddles by play style preference using smart scoring and normalization."""
        
        def score_fn(item):
            p = item["paddle"]
            
            # --- 1. Normalize Metrics (0-10 Scale) ---
            # Power: Use explicit rating if available, else 5
            raw_power = p.power_rating or 5.0
            norm_power = min(max(raw_power, 0), 10)
            
            # Control/Stability: Use Twist Weight (5.0 - 7.5 range)
            # 5.0 -> 0, 7.5 -> 10
            raw_twist = p.twist_weight or 5.0
            norm_control = self._normalize_score(raw_twist, 5.0, 7.5)
            
            # If explicit control rating exists, average it with twist weight proxy
            # (Future proofing if we get better data)
            # if p.control_rating: ...
            
            # --- 2. Calculate Final Score based on Preference ---
            
            # CASE A: Fine-grained Slider Preference (0-100%)
            if profile.power_preference_percent is not None:
                power_weight = profile.power_preference_percent / 100.0
                control_weight = 1.0 - power_weight
                
                # Weighted Average
                final_score = (norm_power * power_weight) + (norm_control * control_weight)
                return final_score

            # CASE B: Legacy Enum Style
            style = profile.play_style
            if style == PlayStyle.POWER:
                return norm_power
            elif style == PlayStyle.CONTROL:
                return norm_control
            else:  # BALANCED
                return (norm_power + norm_control) / 2

        return sorted(paddles_data, key=score_fn, reverse=True)

    def _normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize a value to 0-10 scale based on a range."""
        if value is None:
            return 0.0
        # Linear mapping
        normalized = (value - min_val) / (max_val - min_val) * 10
        return min(max(normalized, 0), 10)

    def _calculate_value_score(self, data: dict, rank: int, profile: UserProfile) -> Optional[float]:
        """Calculate score based on specs vs price."""
        if not data.get("min_price"):
            return None
            
        price = float(data["min_price"])
        if price < 100: # Sanity check for bad data
            return None
            
        # Re-using the ranking score logic would be ideal, but for now let's assume valid data
        # We can approximate the technical score by the rank (higher rank = better score)
        # But a real score is better. Let's do a quick on-the-fly score for value
        # Value = (Performance / Price) * K
        
        # We don't have the raw score here easily without re-running logic or passing it
        # Simplification: Inverse rank / price? No.
        # Let's use the 'power' and 'twist' from the paddle directly
        p = data["paddle"]
        p_rating = p.power_rating or 5
        c_rating = self._normalize_score(p.twist_weight or 5.5, 5.0, 7.5)
        
        avg_tech_score = (p_rating + c_rating) / 2
        
        # Formula: (Score / Price) * 1000 to get a readable number like ~8.5
        # e.g. (8.0 / 1000) * 1000 = 8.0 value score
        # e.g. (8.0 / 2000) * 1000 = 4.0 value score
        
        value_score = (avg_tech_score / price) * 1000
        return round(value_score, 1)
    
    def _get_match_reasons(
        self,
        paddle: PaddleMaster,
        profile: UserProfile
    ) -> list[str]:
        """Generate match reasons for a paddle."""
        reasons = []
        
        if profile.play_style == PlayStyle.POWER and (paddle.power_rating or 0) >= 8:
            reasons.append(f"Alto power rating ({paddle.power_rating}/10)")
        elif profile.play_style == PlayStyle.CONTROL and (paddle.twist_weight or 0) >= 6.5:
            reasons.append(f"Alta estabilidade (Twist Weight {paddle.twist_weight})")
        elif profile.play_style == PlayStyle.BALANCED:
            twist_score = (paddle.twist_weight or 0) * 1.5
            avg = ((paddle.power_rating or 0) + twist_score) / 2
            reasons.append(f"Excelente equilíbrio (Score {avg:.1f}/10)")
        
        if profile.has_tennis_elbow and paddle.ideal_for_tennis_elbow:
            reasons.append("Recomendada para Tennis Elbow")
        
        if paddle.skill_level.value == profile.skill_level.value:
            reasons.append(f"Ideal para nível {profile.skill_level.value}")
        
        return reasons
    
    def _get_tags(
        self,
        paddle: PaddleMaster,
        profile: UserProfile,
        rank: int
    ) -> list[str]:
        """Generate tags for a paddle."""
        tags = []
        
        if rank == 1:
            tags.append("Top Pick")
        
        if (paddle.power_rating or 0) >= 9:
            tags.append("Máximo Power")
        elif (paddle.twist_weight or 0) >= 6.8:
            tags.append("Max Estabilidade")
        
        if paddle.ideal_for_tennis_elbow:
            tags.append("Ergonômica")
        
        return tags
