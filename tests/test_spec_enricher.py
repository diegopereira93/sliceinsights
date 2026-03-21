"""
Tests for spec enricher extractors and update_paddle_specs.

Verifies:
- Unit extraction functions (extract_mm, extract_weight_g, map_face_material, map_shape)
- Free-text spec parsing
- 4-field quality gate in update_paddle_specs
- weight_grams field on PaddleMasterBase
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.scrape_product_specs import (
    extract_mm,
    extract_weight_g,
    map_face_material,
    map_shape,
    parse_freetext_specs,
)
from app.models.paddle import PaddleMasterBase


class TestExtractMm:
    def test_extract_mm_valid_standard(self):
        assert extract_mm("16mm") == 16.0

    def test_extract_mm_valid_decimal_comma(self):
        assert extract_mm("16,5 mm") == 16.5

    def test_extract_mm_valid_uppercase(self):
        assert extract_mm("16MM") == 16.0

    def test_extract_mm_invalid_no_data(self):
        assert extract_mm("no data") is None

    def test_extract_mm_invalid_empty(self):
        assert extract_mm("") is None


class TestExtractWeightG:
    def test_extract_weight_g_valid_g_suffix(self):
        assert extract_weight_g("226.8g") == 226.8

    def test_extract_weight_g_valid_comma(self):
        assert extract_weight_g("226,8 gramas") == 226.8

    def test_extract_weight_g_valid_g_singular(self):
        assert extract_weight_g("230 gram") == 230.0

    def test_extract_weight_g_invalid_no_data(self):
        assert extract_weight_g("no weight") is None

    def test_extract_weight_g_invalid_empty(self):
        assert extract_weight_g("") is None


class TestMapFaceMaterial:
    def test_map_face_material_carbono(self):
        assert map_face_material("carbono") == "CARBON"

    def test_map_face_material_fiberglass(self):
        assert map_face_material("fibra de vidro") == "FIBERGLASS"

    def test_map_face_material_kevlar(self):
        assert map_face_material("kevlar") == "KEVLAR"

    def test_map_face_material_hybrid(self):
        assert map_face_material("híbrido") == "HYBRID"

    def test_map_face_material_invalid(self):
        assert map_face_material("titanium") is None


class TestMapShape:
    def test_map_shape_elongada(self):
        assert map_shape("elongada") == "ELONGATED"

    def test_map_shape_standard(self):
        assert map_shape("standard") == "STANDARD"

    def test_map_shape_widebody(self):
        assert map_shape("wide body") == "WIDEBODY"

    def test_map_shape_invalid(self):
        assert map_shape("circular") is None


class TestParseFreetextSpecs:
    def test_parse_freetext_specs_complete(self):
        text = "Raquete com 16mm de espessura, carbono, 226g, formato elongada"
        specs = parse_freetext_specs(text)
        assert specs.get("core_thickness_mm") == 16.0
        assert specs.get("face_material") == "CARBON"
        assert specs.get("weight_grams") == 226.0
        assert specs.get("shape") == "ELONGATED"

    def test_parse_freetext_specs_partial(self):
        text = "Raquete de carbono, 14mm de espessura"
        specs = parse_freetext_specs(text)
        assert specs.get("core_thickness_mm") == 14.0
        assert specs.get("face_material") == "CARBON"
        assert "weight_grams" not in specs


class TestFourFieldGate:
    def test_weight_grams_renamed(self):
        text = "Raquete com 16mm, carbono, 226g, formato elongada"
        specs = parse_freetext_specs(text)
        assert "weight_grams" in specs
        assert "weight_g" not in specs

    def test_four_field_gate_complete(self):
        from unittest.mock import MagicMock, patch
        from app.models.paddle import PaddleMaster
        from app.models.enums import FaceMaterial, PaddleShape

        mock_paddle = MagicMock(spec=PaddleMaster)
        mock_paddle.core_thickness_mm = None
        mock_paddle.face_material = None
        mock_paddle.shape = None
        mock_paddle.weight_grams = None
        mock_paddle.validation_sources = []

        mock_session = MagicMock()
        mock_brand = MagicMock()
        mock_brand.id = 1
        mock_session.exec.return_value.first.side_effect = [mock_brand, mock_paddle]

        specs = {
            "brand_name": "Test Brand",
            "model_name": "Test Model",
            "core_thickness_mm": 16.0,
            "face_material": "CARBON",
            "weight_grams": 226.0,
            "shape": "ELONGATED",
        }

        from scripts.scrape_product_specs import update_paddle_specs
        result = update_paddle_specs(specs, "test_store", mock_session)

        assert result is True
        assert mock_paddle.core_thickness_mm == 16.0
        assert mock_paddle.face_material == FaceMaterial.CARBON
        assert mock_paddle.shape == PaddleShape.ELONGATED
        assert mock_paddle.weight_grams == 226.0
        mock_session.add.assert_called_once_with(mock_paddle)

    def test_four_field_gate_partial(self):
        from unittest.mock import MagicMock

        mock_session = MagicMock()
        mock_brand = MagicMock()
        mock_brand.id = 1
        mock_session.exec.return_value.first.side_effect = [mock_brand, None]

        specs = {
            "brand_name": "Test Brand",
            "model_name": "Test Model",
            "core_thickness_mm": 16.0,
            "face_material": "CARBON",
            # missing weight_grams and shape
        }

        from scripts.scrape_product_specs import update_paddle_specs
        result = update_paddle_specs(specs, "test_store", mock_session)

        assert result is False

    def test_validation_source_recorded(self):
        from unittest.mock import MagicMock
        from app.models.paddle import PaddleMaster
        from app.models.enums import FaceMaterial, PaddleShape

        mock_paddle = MagicMock(spec=PaddleMaster)
        mock_paddle.core_thickness_mm = None
        mock_paddle.face_material = None
        mock_paddle.shape = None
        mock_paddle.weight_grams = None
        mock_paddle.validation_sources = []

        mock_session = MagicMock()
        mock_brand = MagicMock()
        mock_brand.id = 1
        mock_session.exec.return_value.first.side_effect = [mock_brand, mock_paddle]

        specs = {
            "brand_name": "Test Brand",
            "model_name": "Test Model",
            "core_thickness_mm": 16.0,
            "face_material": "CARBON",
            "weight_grams": 226.0,
            "shape": "ELONGATED",
        }

        from scripts.scrape_product_specs import update_paddle_specs
        result = update_paddle_specs(specs, "joola", mock_session)

        assert result is True
        assert "scraping_joola" in mock_paddle.validation_sources


class TestWeightGramsFieldExists:
    def test_weight_grams_field_exists(self):
        assert "weight_grams" in PaddleMasterBase.model_fields

    def test_weight_grams_default_none(self):
        paddle = PaddleMasterBase(model_name="Test Paddle")
        assert paddle.weight_grams is None
