import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.recommendation_engine import RecommendationEngine, PlayStyle
from app.schemas.user_profile import UserProfile
from decimal import Decimal
import uuid

class MockPaddle:
    def __init__(self, id=None, power_rating=None, twist_weight=None, control_rating=None, spin_rating=None, name="Paddle", spin_rpm=2200):
        self.id = id or uuid.uuid4()
        self.power_rating = power_rating or 5
        self.twist_weight = twist_weight or 6.0
        self.control_rating = control_rating or 5
        self.spin_rating = spin_rating or 5
        self.spin_rpm = spin_rpm
        self.model_name = name
        self.skill_level = MagicMock(value="intermediate")
        self.ideal_for_tennis_elbow = False
        self.core_thickness_mm = 16.0
        self.brand_id = 1
        self.brand = MagicMock()
        self.brand.name = "Test Brand"

def test_normalization():
    engine = RecommendationEngine(session=None)
    assert engine._normalize_score(5.0, 5.0, 7.5) == 0.0
    assert engine._normalize_score(7.5, 5.0, 7.5) == 10.0
    assert engine._normalize_score(6.25, 5.0, 7.5) == 5.0

def test_ranking_logic_slider():
    engine = RecommendationEngine(session=None)
    p1 = {"paddle": MockPaddle(power_rating=9.0, twist_weight=5.5, name="PowerPaddle")} 
    p2 = {"paddle": MockPaddle(power_rating=5.0, twist_weight=7.5, name="ControlPaddle")} 
    data = [p1, p2]
    
    # 50/50 Balanced
    profile_50p = UserProfile(skill_level="intermediate", play_style=PlayStyle.BALANCED, power_preference_percent=50)
    
    # Calculate ratings first as the engine expects them in the item
    from app.models.paddle import calculate_paddle_ratings
    p1["ratings"] = calculate_paddle_ratings(p1["paddle"])
    p2["ratings"] = calculate_paddle_ratings(p2["paddle"])
    
    ranked = engine._rank_by_style(data, profile_50p)
    assert ranked[0]["paddle"].model_name == "PowerPaddle"

def test_value_score():
    engine = RecommendationEngine(session=None)
    profile = UserProfile(skill_level="intermediate", play_style=PlayStyle.BALANCED)
    pA = MockPaddle(power_rating=8.0, twist_weight=7.5) # Avg 9.0
    from app.models.paddle import calculate_paddle_ratings
    data_A = {"paddle": pA, "min_price": 1000, "ratings": calculate_paddle_ratings(pA)}
    score_A = engine._calculate_value_score(data_A, profile)
    # performance = (8.0 + 10.0 + 10.0) / 3 = 9.333
    # value = (9.333 / 1000) * 1000 = 9.3
    assert score_A == 9.3

@pytest.mark.asyncio
async def test_cache_logic():
    mock_session = AsyncMock()
    # Mocking rows return for a query
    p_id = uuid.uuid4()
    mock_row = (MockPaddle(id=p_id), "BrandX", Decimal("1000"), 1)
    
    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row]
    mock_session.exec.return_value = mock_result
    
    engine = RecommendationEngine(session=mock_session)
    profile = UserProfile(skill_level="intermediate", play_style=PlayStyle.BALANCED)
    
    # First call: Should hit DB
    res1 = await engine.get_recommendations(profile, limit=1)
    assert mock_session.exec.call_count == 1
    
    # Second call: Should hit Cache
    res2 = await engine.get_recommendations(profile, limit=1)
    assert mock_session.exec.call_count == 1 # Still 1
    assert res1 == res2
    assert res2.recommendations[0].paddle_id == p_id
