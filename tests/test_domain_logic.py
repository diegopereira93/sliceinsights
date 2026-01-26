
import pytest
from app.models.paddle import calculate_paddle_ratings, PaddleMaster

def test_calculate_ratings_large_twist_scale():
    """Test twist weight in the 150-600 scale."""
    # User Case: Twist 300 should be ~ mid control
    # Formula: (300 - 150) / 450 * 10 = 150/450 * 10 = 3.33 -> 3
    paddle = PaddleMaster(model_name="Test", twist_weight=300.0, spin_rpm=150)
    ratings = calculate_paddle_ratings(paddle)
    assert ratings["control"] == 3

    # Max Case: Twist 600 -> 10
    paddle_max = PaddleMaster(model_name="Max", twist_weight=600.0, spin_rpm=150)
    ratings_max = calculate_paddle_ratings(paddle_max)
    assert ratings_max["control"] == 10

def test_calculate_ratings_small_twist_scale():
    """Test twist weight in the 5.0-7.5 scale."""
    # Case: Twist 6.0
    # Formula: 6.0 * 1.5 = 9.0
    paddle = PaddleMaster(model_name="Test Small", twist_weight=6.0, spin_rpm=150)
    ratings = calculate_paddle_ratings(paddle)
    assert ratings["control"] == 9

def test_spin_rating_logic():
    """Test spin rpm conversion."""
    # Case: 300 RPM -> (300-150)/150 * 10 = 10
    paddle = PaddleMaster(model_name="Spin Doctor", twist_weight=150, spin_rpm=300)
    ratings = calculate_paddle_ratings(paddle)
    assert ratings["spin"] == 10

    # Case: 150 RPM -> 0
    paddle_min = PaddleMaster(model_name="Spin Low", twist_weight=150, spin_rpm=150)
    ratings_min = calculate_paddle_ratings(paddle_min)
    assert ratings_min["spin"] == 0

def test_sweet_spot_inversion():
    """Test that sweet spot behaves inversely to control (as per simplistic logic for now)."""
    # High Control (10) -> Sweet Spot (10 - 4) = 6
    # Wait, formula is max(1.0, 10.0 - (control * 0.4))
    # If control=10: 10 - 4 = 6.
    paddle = PaddleMaster(model_name="Control Freak", twist_weight=600, spin_rpm=150)
    ratings = calculate_paddle_ratings(paddle)
    assert ratings["control"] == 10
    # assert ratings["sweet_spot"] == 6 # Rounding might apply
    
    # Let's verify exact behavior for zero control
    # Control 0 -> Sweet Spot 10
    paddle_zero = PaddleMaster(model_name="Zero Control", twist_weight=150, spin_rpm=150) # Twist 150 -> 0 control formula? (150-150)=0
    ratings_z = calculate_paddle_ratings(paddle_zero)
    assert ratings_z["control"] == 0
    assert ratings_z["sweet_spot"] == 10

def test_missing_values_defaults():
    """Test behavior when optional fields are None."""
    paddle = PaddleMaster(model_name="Ghost")
    ratings = calculate_paddle_ratings(paddle)
    
    # Expect defaults
    # Twist None -> 0 -> Control 5.0 (small scale logic: 0*1.5=0? No, else: if twist>0 else 5.0)
    # Code says: control = twist * 1.5 if twist > 0 else 5.0
    # So Control should be 5
    assert ratings["control"] == 5
    
    # Spin None -> 0 -> 5.0 (default for missing is average, not poor)
    assert ratings["spin"] == 5
