"""
Tests for Phase 1 Data Quality functions.

Tests calculate_specs_confidence, calculate_control, and the updated
calculate_paddle_ratings (control via core_thickness_mm).
"""
import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from app.models.paddle import (
    calculate_specs_confidence,
    calculate_control,
    calculate_paddle_ratings,
    REQUIRED_FIELDS,
)
from app.models.enums import FaceMaterial, PaddleShape


def _make_paddle(**overrides):
    """Create a mock paddle with all required fields filled by default."""
    defaults = {
        'core_thickness_mm': 16.0,
        'face_material': FaceMaterial.CARBON,
        'core_material': 'Polymer Honeycomb',
        'shape': PaddleShape.ELONGATED,
        'swing_weight': 115,
        'spin_rpm': 2200,
        'power_rating': 8,
        'handle_length': '5.5',
        # Non-required fields
        'twist_weight': 6.5,
        'power_original': 8.5,
        'grip_circumference': '4.125',
        'validation_sources': [],
    }
    defaults.update(overrides)
    paddle = MagicMock()
    for k, v in defaults.items():
        setattr(paddle, k, v)
    return paddle


# ═══════════════════════════════════════════════════════════════════════════════
# calculate_specs_confidence
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculateSpecsConfidence:
    def test_2_sources_returns_1(self):
        paddle = _make_paddle(validation_sources=["johnkew", "pbstudio"])
        assert calculate_specs_confidence(paddle) == 1.0

    def test_all_fields_filled_returns_1(self):
        paddle = _make_paddle()
        assert calculate_specs_confidence(paddle) == 1.0

    def test_1_source_not_all_fields_returns_0_5(self):
        paddle = _make_paddle(validation_sources=["pbstudio"], swing_weight=None)
        assert calculate_specs_confidence(paddle) == 0.5

    def test_no_sources_not_all_fields_returns_0(self):
        for field in REQUIRED_FIELDS:
            paddle = _make_paddle(**{field: None})
            assert calculate_specs_confidence(paddle) == 0.0, (
                f"Expected 0.0 when {field} is None"
            )

    def test_all_fields_missing_returns_0(self):
        paddle = _make_paddle(**{f: None for f in REQUIRED_FIELDS})
        assert calculate_specs_confidence(paddle) == 0.0

    def test_non_required_fields_dont_affect(self):
        paddle = _make_paddle(twist_weight=None, grip_circumference=None)
        assert calculate_specs_confidence(paddle) == 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# calculate_control
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculateControl:
    def test_none_returns_none(self):
        assert calculate_control(None) is None

    def test_13mm(self):
        result = calculate_control(13.0)
        assert result == 1  # (13-12)/7*10 = 1.43 → 1

    def test_14mm(self):
        result = calculate_control(14.0)
        assert result == 3  # (14-12)/7*10 = 2.86 → 3

    def test_16mm(self):
        result = calculate_control(16.0)
        assert result == 6  # (16-12)/7*10 = 5.71 → 6

    def test_19mm(self):
        result = calculate_control(19.0)
        assert result == 10  # (19-12)/7*10 = 10.0 → 10

    def test_12mm_floor(self):
        result = calculate_control(12.0)
        assert result == 0  # (12-12)/7*10 = 0 → 0

    def test_very_thick_capped_at_10(self):
        result = calculate_control(25.0)
        assert result == 10

    def test_very_thin_capped_at_0(self):
        result = calculate_control(10.0)
        assert result == 0


# ═══════════════════════════════════════════════════════════════════════════════
# calculate_paddle_ratings (integration)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculatePaddleRatings:
    def test_control_uses_core_thickness_not_twist_weight(self):
        paddle = _make_paddle(core_thickness_mm=16.0, twist_weight=999)
        ratings = calculate_paddle_ratings(paddle)
        assert ratings['control'] == 6  # From core_thickness_mm, NOT twist_weight

    def test_control_none_when_no_thickness(self):
        paddle = _make_paddle(core_thickness_mm=None, twist_weight=6.5)
        ratings = calculate_paddle_ratings(paddle)
        assert ratings['control'] is None

    def test_all_ratings_present_when_complete(self):
        paddle = _make_paddle()
        ratings = calculate_paddle_ratings(paddle)
        assert ratings['power'] is not None
        assert ratings['control'] is not None
        assert ratings['spin'] is not None
        assert ratings['sweet_spot'] is not None
        assert ratings['has_incomplete_data'] is False

    def test_has_incomplete_data_true_when_missing(self):
        paddle = _make_paddle(core_thickness_mm=None, spin_rpm=None)
        ratings = calculate_paddle_ratings(paddle)
        assert ratings['has_incomplete_data'] is True

    def test_sweet_spot_depends_on_control(self):
        paddle = _make_paddle(core_thickness_mm=16.0)
        ratings = calculate_paddle_ratings(paddle)
        assert ratings['sweet_spot'] is not None

        paddle_no_control = _make_paddle(core_thickness_mm=None)
        ratings_nc = calculate_paddle_ratings(paddle_no_control)
        assert ratings_nc['sweet_spot'] is None

    def test_spin_rpm_mapping(self):
        paddle = _make_paddle(spin_rpm=300)
        ratings = calculate_paddle_ratings(paddle)
        # (300-150)/150*10 = 10 → capped at 10
        assert ratings['spin'] == 10

    def test_spin_rpm_zero(self):
        paddle = _make_paddle(spin_rpm=0)
        ratings = calculate_paddle_ratings(paddle)
        assert ratings['spin'] == 5  # 0 RPM → 5.0

    def test_power_from_power_rating(self):
        paddle = _make_paddle(power_rating=7)
        ratings = calculate_paddle_ratings(paddle)
        assert ratings['power'] == 7


# ═══════════════════════════════════════════════════════════════════════════════
# Inference Functions (Phase 2)
# ═══════════════════════════════════════════════════════════════════════════════

class TestInferFaceMaterial:
    def test_raw_carbon_fiber(self):
        from app.models.enums import FaceMaterial
        from scripts.enrich_from_csv import infer_face_material
        assert infer_face_material("Raw carbon fiber") == FaceMaterial.CARBON

    def test_3k_carbon_fiber(self):
        from app.models.enums import FaceMaterial
        from scripts.enrich_from_csv import infer_face_material
        assert infer_face_material("3k carbon fiber") == FaceMaterial.CARBON

    def test_kevlar(self):
        from app.models.enums import FaceMaterial
        from scripts.enrich_from_csv import infer_face_material
        assert infer_face_material("Kevlar") == FaceMaterial.KEVLAR

    def test_composite_is_fiberglass(self):
        from app.models.enums import FaceMaterial
        from scripts.enrich_from_csv import infer_face_material
        assert infer_face_material("(Composite)") == FaceMaterial.FIBERGLASS

    def test_titanium_is_hybrid(self):
        from app.models.enums import FaceMaterial
        from scripts.enrich_from_csv import infer_face_material
        assert infer_face_material("titanium (polyester threads)") == FaceMaterial.HYBRID


class TestInferShape:
    def test_wide_body(self):
        from app.models.enums import PaddleShape
        from scripts.enrich_from_csv import infer_shape
        assert infer_shape("Wide body") == PaddleShape.WIDEBODY

    def test_hybrid_is_standard(self):
        from app.models.enums import PaddleShape
        from scripts.enrich_from_csv import infer_shape
        assert infer_shape("Hybrid") == PaddleShape.STANDARD

    def test_extra_elongated(self):
        from app.models.enums import PaddleShape
        from scripts.enrich_from_csv import infer_shape
        assert infer_shape("Extra Elongated") == PaddleShape.ELONGATED

    def test_model_name_widebody(self):
        from app.models.enums import PaddleShape
        from scripts.enrich_from_csv import infer_shape
        assert infer_shape("Labs Project Boom Stik Widebody 16mm") == PaddleShape.WIDEBODY

    def test_model_name_elongated(self):
        from app.models.enums import PaddleShape
        from scripts.enrich_from_csv import infer_shape
        assert infer_shape("ERA Enlongated 16mm") == PaddleShape.ELONGATED
