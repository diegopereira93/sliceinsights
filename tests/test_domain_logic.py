from app.models.paddle import calculate_paddle_ratings, calculate_control, PaddleMaster


def test_calculate_control_from_core_thickness():
    """Control is now derived from core_thickness_mm, NOT twist_weight."""
    # 13mm → 1, 16mm → 6, 19mm → 10
    paddle_13 = PaddleMaster(model_name="Thin", core_thickness_mm=13.0, spin_rpm=150)
    ratings_13 = calculate_paddle_ratings(paddle_13)
    assert ratings_13["control"] == 1

    paddle_16 = PaddleMaster(model_name="Mid", core_thickness_mm=16.0, spin_rpm=150)
    ratings_16 = calculate_paddle_ratings(paddle_16)
    assert ratings_16["control"] == 6

    paddle_19 = PaddleMaster(model_name="Thick", core_thickness_mm=19.0, spin_rpm=150)
    ratings_19 = calculate_paddle_ratings(paddle_19)
    assert ratings_19["control"] == 10


def test_twist_weight_no_longer_affects_control():
    """twist_weight remains as data but does NOT calculate control rating."""
    paddle = PaddleMaster(model_name="Legacy", twist_weight=600.0, spin_rpm=150)
    ratings = calculate_paddle_ratings(paddle)
    # Without core_thickness_mm, control must be None
    assert ratings["control"] is None


def test_spin_rating_logic():
    """Test spin rpm conversion."""
    # Case: 300 RPM -> (300-150)/150 * 10 = 10
    paddle = PaddleMaster(model_name="Spin Doctor", core_thickness_mm=16.0, spin_rpm=300)
    ratings = calculate_paddle_ratings(paddle)
    assert ratings["spin"] == 10

    # Case: 150 RPM -> 0
    paddle_min = PaddleMaster(model_name="Spin Low", core_thickness_mm=16.0, spin_rpm=150)
    ratings_min = calculate_paddle_ratings(paddle_min)
    assert ratings_min["spin"] == 0


def test_sweet_spot_inversion():
    """Sweet spot behaves inversely to control (10 - control * 0.4)."""
    # High Control (10, core=19mm) -> Sweet Spot = 10 - 4 = 6
    paddle = PaddleMaster(model_name="Control Freak", core_thickness_mm=19.0, spin_rpm=150)
    ratings = calculate_paddle_ratings(paddle)
    assert ratings["control"] == 10
    assert ratings["sweet_spot"] == 6

    # Low Control (0, core=12mm) -> Sweet Spot = 10
    paddle_zero = PaddleMaster(model_name="Zero Control", core_thickness_mm=12.0, spin_rpm=150)
    ratings_z = calculate_paddle_ratings(paddle_zero)
    assert ratings_z["control"] == 0
    assert ratings_z["sweet_spot"] == 10


def test_missing_values_returns_none():
    """Test behavior when optional fields are None — ratings must be None, not fabricated."""
    paddle = PaddleMaster(model_name="Ghost")
    paddle.id = "00000000-0000-0000-0000-000000000000"
    ratings = calculate_paddle_ratings(paddle)

    assert ratings["control"] is None
    assert ratings["spin"] is None
    assert ratings["sweet_spot"] is None
    assert ratings["power"] is None
    assert ratings["has_incomplete_data"] is True
