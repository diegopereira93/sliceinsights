"""
User profile and recommendation schemas for API requests/responses.
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.enums import SkillLevel, PlayStyle


class UserProfile(BaseModel):
    """User profile for recommendation input."""
    skill_level: SkillLevel = Field(description="Player skill level")
    budget_max_brl: Optional[float] = Field(
        default=None,
        gt=0,
        description="Maximum budget in BRL"
    )
    play_style: PlayStyle = Field(description="Preferred play style")
    has_tennis_elbow: bool = Field(
        default=False,
        description="Whether user has tennis elbow condition"
    )
    spin_preference: Optional[str] = Field(
        default=None,
        description="Spin preference: high, medium, or low"
    )
    weight_preference: Optional[str] = Field(
        default=None,
        description="Weight preference: heavy, standard, light, or no_preference"
    )
    power_preference_percent: Optional[int] = Field(
        default=None,
        ge=0,
        le=100,
        description="Fine preference: 0=Control (100% Control), 100=Power (100% Power), 50=Balanced"
    )


class PaddleRecommendation(BaseModel):
    """Single paddle recommendation."""
    rank: int
    paddle_id: UUID
    brand_name: str
    model_name: str
    ratings: dict[str, int]
    min_price_brl: Optional[float]
    match_reasons: list[str]
    tags: list[str]
    value_score: Optional[float] = None


class RecommendationResult(BaseModel):
    """Full recommendation response."""
    user_profile: UserProfile
    recommendations: list[PaddleRecommendation]
    filters_applied: dict[str, bool]
    total_matching: int
    returned: int


class RecommendationRequest(BaseModel):
    """API request for recommendations."""
    skill_level: SkillLevel
    budget_max_brl: Optional[float] = Field(default=None, gt=0)
    play_style: PlayStyle
    has_tennis_elbow: bool = False
    spin_preference: Optional[str] = Field(default=None)
    weight_preference: Optional[str] = Field(default=None)
    power_preference_percent: Optional[int] = Field(default=None, ge=0, le=100)
    limit: int = Field(default=3, ge=1, le=10)

