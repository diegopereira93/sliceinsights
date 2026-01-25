
# import pytest (removed)
from app.services.recommendation_engine import RecommendationEngine, PlayStyle
from app.schemas.user_profile import UserProfile

# Mocking PaddleMaster since we don't have DB access here
class MockPaddle:
    def __init__(self, power_rating=None, twist_weight=None, control_rating=None, price=None, name="Paddle"):
        self.power_rating = power_rating
        self.twist_weight = twist_weight
        self.control_rating = control_rating
        self.price = price
        self.name = name
        self.model_name = name

def test_normalization():
    engine = RecommendationEngine(session=None)
    
    # Test Swing Weight / Twist Weight Normalization
    # Range 5.0 - 7.5
    assert engine._normalize_score(5.0, 5.0, 7.5) == 0.0
    assert engine._normalize_score(7.5, 5.0, 7.5) == 10.0
    assert engine._normalize_score(6.25, 5.0, 7.5) == 5.0
    
    # Check clamping
    assert engine._normalize_score(4.0, 5.0, 7.5) == 0.0
    assert engine._normalize_score(8.0, 5.0, 7.5) == 10.0

def test_ranking_logic_legacy_enum():
    engine = RecommendationEngine(session=None)
    
    p1 = {"paddle": MockPaddle(power_rating=9.0, twist_weight=5.5, name="PowerPaddle")} # Norm Twist: ~2.0
    p2 = {"paddle": MockPaddle(power_rating=5.0, twist_weight=7.5, name="ControlPaddle")} # Norm Twist: 10.0
    
    data = [p1, p2]
    
    # 1. Test Power Preference
    profile_power = UserProfile(skill_level="intermediate", play_style=PlayStyle.POWER)
    ranked_power = engine._rank_by_style(data, profile_power)
    assert ranked_power[0]["paddle"].name == "PowerPaddle"
    
    # 2. Test Control Preference
    profile_control = UserProfile(skill_level="intermediate", play_style=PlayStyle.CONTROL)
    ranked_control = engine._rank_by_style(data, profile_control)
    assert ranked_control[0]["paddle"].name == "ControlPaddle"

def test_ranking_logic_slider():
    engine = RecommendationEngine(session=None)
    
    # P1: High Power (9), Low Stability (2)
    p1 = {"paddle": MockPaddle(power_rating=9.0, twist_weight=5.5, name="PowerPaddle")} 
    # P2: Low Power (5), High Stability (10)
    p2 = {"paddle": MockPaddle(power_rating=5.0, twist_weight=7.5, name="ControlPaddle")} 
    
    data = [p1, p2]
    
    # 1. 100% Power (Should match Enum Power)
    profile_100p = UserProfile(skill_level="intermediate", play_style=PlayStyle.BALANCED, power_preference_percent=100)
    ranked = engine._rank_by_style(data, profile_100p)
    assert ranked[0]["paddle"].name == "PowerPaddle"
    
    # 2. 100% Control (0% Power)
    profile_0p = UserProfile(skill_level="intermediate", play_style=PlayStyle.BALANCED, power_preference_percent=0)
    ranked = engine._rank_by_style(data, profile_0p)
    assert ranked[0]["paddle"].name == "ControlPaddle"
    
    # 3. 50/50 Balanced
    # P1 Score: (9 * 0.5) + (2 * 0.5) = 4.5 + 1.0 = 5.5
    # P2 Score: (5 * 0.5) + (10 * 0.5) = 2.5 + 5.0 = 7.5
    # P2 should win
    profile_50p = UserProfile(skill_level="intermediate", play_style=PlayStyle.BALANCED, power_preference_percent=50)
    ranked = engine._rank_by_style(data, profile_50p)
    assert ranked[0]["paddle"].name == "ControlPaddle"

def test_value_score():
    engine = RecommendationEngine(session=None)
    profile = UserProfile(skill_level="intermediate", play_style=PlayStyle.BALANCED)
    
    # Paddle A: High Tech Score (avg ~8), Price 1000
    pA = MockPaddle(power_rating=8.0, twist_weight=7.5) # Tw=10 -> Avg 9.0
    data_A = {"paddle": pA, "min_price": 1000}
    
    # Paddle B: Same Tech Score, Price 2000
    pB = MockPaddle(power_rating=8.0, twist_weight=7.5)
    data_B = {"paddle": pB, "min_price": 2000}
    
    score_A = engine._calculate_value_score(data_A, 1, profile)
    score_B = engine._calculate_value_score(data_B, 1, profile)
    
    # Score A should be double Score B
    assert score_A > score_B
    assert score_A == 9.0 # (9.0 / 1000) * 1000
    assert score_B == 4.5 # (9.0 / 2000) * 1000

if __name__ == "__main__":
    # Simple manual run wrapper if pytest is not installed/wanted
    try:
        test_normalization()
        test_ranking_logic_legacy_enum()
        test_ranking_logic_slider()
        test_value_score()
        print("All Tests Passed!")
    except AssertionError as e:
        print(f"Test Failed: {e}")
        exit(1)
