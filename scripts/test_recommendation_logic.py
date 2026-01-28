
import os
import sys

# Add current directory to path to find 'app'
sys.path.append(os.getcwd())

from app.services.recommendation_engine import RecommendationEngine
from app.models.enums import PlayStyle
from app.schemas.user_profile import UserProfile
from app.models.paddle import calculate_paddle_ratings

# Mocking PaddleMaster since we don't have DB access here
class MockPaddle:
    def __init__(self, power_rating=None, twist_weight=None, spin_rpm=None, price=None, name="Paddle"):
        self.power_rating = power_rating
        self.twist_weight = twist_weight
        self.spin_rpm = spin_rpm
        self.price = price
        self.name = name
        self.model_name = name
        self.core_thickness_mm = 16.0 # Default
        self.id = "test-uuid"
        self.brand_id = 1
        self.brand = None

def get_paddles_data(paddles):
    data = []
    for p in paddles:
        ratings = calculate_paddle_ratings(p)
        data.append({
            "paddle": p,
            "ratings": ratings,
            "min_price": getattr(p, 'price', None),
            "brand_name": "Test Brand"
        })
    return data

def test_normalization():
    engine = RecommendationEngine(session=None)
    
    # Test Generic Normalization (0-10 scale)
    assert engine._normalize_score(5.0, 5.0, 7.5) == 0.0
    assert engine._normalize_score(7.5, 5.0, 7.5) == 10.0
    assert engine._normalize_score(6.25, 5.0, 7.5) == 5.0
    
    # Check clamping
    assert engine._normalize_score(4.0, 5.0, 7.5) == 0.0
    assert engine._normalize_score(8.0, 5.0, 7.5) == 10.0

def test_ranking_logic_legacy_enum():
    engine = RecommendationEngine(session=None)
    
    # PowerPaddle: High Power Rating (9), Low Twist Weight (5.0 -> Control ~7.5)
    p1 = MockPaddle(power_rating=9.0, twist_weight=5.0, name="PowerPaddle")
    # ControlPaddle: Low Power Rating (5), High Twist Weight (6.5 -> Control ~9.75)
    p2 = MockPaddle(power_rating=5.0, twist_weight=6.5, name="ControlPaddle")
    
    data = get_paddles_data([p1, p2])
    
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
    
    p1 = MockPaddle(power_rating=9.0, twist_weight=5.0, name="PowerPaddle") 
    p2 = MockPaddle(power_rating=3.0, twist_weight=6.5, name="ControlPaddle") 
    
    data = get_paddles_data([p1, p2])
    
    # 1. 100% Power
    profile_100p = UserProfile(skill_level="intermediate", play_style=PlayStyle.BALANCED, power_preference_percent=100)
    ranked = engine._rank_by_style(data, profile_100p)
    assert ranked[0]["paddle"].name == "PowerPaddle"
    
    # 2. 100% Control (0% Power)
    profile_0p = UserProfile(skill_level="intermediate", play_style=PlayStyle.BALANCED, power_preference_percent=0)
    ranked = engine._rank_by_style(data, profile_0p)
    assert ranked[0]["paddle"].name == "ControlPaddle"

def test_value_score():
    engine = RecommendationEngine(session=None)
    profile = UserProfile(skill_level="intermediate", play_style=PlayStyle.BALANCED)
    
    # Paddle A: High Tech Score (Avg ~9.3), Price 1000
    # Calculations: 
    # Power=9.0, Twist=6.0 (Control=9.0), Spin=150 (Spin=0.0?? wait)
    # Ah, spin_rpm >= 150 -> (150-150)/150 = 0.0. 
    # Let's use spin_rpm=300 for Spin=10.0
    pA = MockPaddle(power_rating=9.0, twist_weight=6.0, spin_rpm=300, price=1000)
    data_A = get_paddles_data([pA])[0]
    
    # Paddle B: Same Tech Score, Price 2000
    pB = MockPaddle(power_rating=9.0, twist_weight=6.0, spin_rpm=300, price=2000)
    data_B = get_paddles_data([pB])[0]
    
    score_A = engine._calculate_value_score(data_A, profile)
    score_B = engine._calculate_value_score(data_B, profile)
    
    # Ratings A/B:
    # Power=9.0, Control=9.0, Spin=10.0
    # Avg Performance = (9+9+10)/3 = 9.333
    # A Score = (9.333 / 1000) * 1000 = 9.3
    # B Score = (9.333 / 2000) * 1000 = 4.7
    
    assert score_A > score_B
    assert score_A == 9.3
    assert score_B == 4.7

if __name__ == "__main__":
    try:
        test_normalization()
        test_ranking_logic_legacy_enum()
        test_ranking_logic_slider()
        test_value_score()
        print("✅ Recommendation Logic Tests Passed!")
    except AssertionError:
        print("❌ Test Failed")
        # Find which frame failed to be more specific
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
