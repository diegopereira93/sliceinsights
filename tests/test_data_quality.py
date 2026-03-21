"""
Tests for Phase 1 Data Quality functions.

Tests calculate_specs_confidence, calculate_control, and the updated
calculate_paddle_ratings (control via core_thickness_mm).
"""
from unittest.mock import MagicMock

from app.models.paddle import (
    calculate_specs_confidence,
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
        'image_url': 'http://example.com/image.png',
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
