"""Tests for app.db.ingestor — paddle filtering, normalization, and DB ingestion."""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.db.ingestor import ingest_rows, is_paddle, normalize, SKIP_KEYWORDS


class TestIsPaddle:
    """Tests for is_paddle() — filters non-paddle products."""

    def test_accepts_paddle(self):
        assert is_paddle({"model_name": "Power Air", "brand_name": "Selkirk"}) is True

    def test_rejects_bag(self):
        assert is_paddle({"model_name": "Mochila Pro Tour", "brand_name": "Selkirk"}) is False

    def test_rejects_ball(self):
        assert is_paddle({"model_name": "Bola Outdoor X", "brand_name": "Franklin"}) is False

    def test_rejects_grip(self):
        assert is_paddle({"model_name": "Overgrip Pack 3", "brand_name": "Wilson"}) is False

    def test_rejects_shoes(self):
        assert is_paddle({"model_name": "Tenis Court Pro", "brand_name": "Head"}) is False

    def test_rejects_apparel(self):
        assert is_paddle({"model_name": "Camiseta Dry Fit", "brand_name": "JOOLA"}) is False

    def test_empty_model_is_paddle(self):
        assert is_paddle({"model_name": "", "brand_name": ""}) is True

    def test_case_insensitive(self):
        assert is_paddle({"model_name": "BOLSA Grande", "brand_name": "Test"}) is False


class TestNormalize:
    """Tests for normalize() — whitespace + title-case."""

    def test_basic(self):
        assert normalize("  selkirk  power  air  ") == "Selkirk Power Air"

    def test_already_normalized(self):
        assert normalize("Selkirk") == "Selkirk"


class TestIngestRows:
    """Tests for ingest_rows() — brand/paddle dedup + market_offer upsert."""

    def _make_mock_session(self):
        session = MagicMock()
        session.exec.return_value.first.return_value = None
        return session

    def test_creates_brand_paddle_offer(self):
        session = self._make_mock_session()
        rows = [{"brand_name": "Selkirk", "model_name": "Power Air", "price_brl": "1500.00", "product_url": "https://example.com/p1", "image_url": ""}]
        result = ingest_rows(rows, store_id=1, session=session)
        assert result["created"] == 1
        assert result["skipped"] == 0
        assert session.add.call_count >= 3
        assert session.flush.call_count >= 2

    def test_skips_non_paddle(self):
        session = self._make_mock_session()
        rows = [{"brand_name": "Selkirk", "model_name": "Mochila Pro", "price_brl": "200.00", "product_url": "https://example.com/bag", "image_url": ""}]
        result = ingest_rows(rows, store_id=1, session=session)
        assert result["skipped"] == 1
        assert result["created"] == 0

    def test_skips_invalid_price(self):
        session = self._make_mock_session()
        rows = [{"brand_name": "Selkirk", "model_name": "Power Air", "price_brl": "invalid", "product_url": "https://example.com/p1", "image_url": ""}]
        result = ingest_rows(rows, store_id=1, session=session)
        assert result["skipped"] == 1

    def test_skips_zero_price(self):
        session = self._make_mock_session()
        rows = [{"brand_name": "Selkirk", "model_name": "Power Air", "price_brl": "0", "product_url": "https://example.com/p1", "image_url": ""}]
        result = ingest_rows(rows, store_id=1, session=session)
        assert result["skipped"] == 1

    def test_skips_excluded_brand(self):
        session = self._make_mock_session()
        rows = [{"brand_name": "nan", "model_name": "Power Air", "price_brl": "1500.00", "product_url": "https://example.com/p1", "image_url": ""}]
        result = ingest_rows(rows, store_id=1, session=session)
        assert result["skipped"] == 1

    def test_updates_existing_offer(self):
        session = MagicMock()
        existing_brand = MagicMock()
        existing_brand.id = 1
        existing_paddle = MagicMock()
        existing_paddle.id = "uuid-123"
        existing_offer = MagicMock()
        existing_offer.price_brl = Decimal("1000.00")

        session.exec.return_value.first.side_effect = [existing_brand, existing_paddle, existing_offer]

        rows = [{"brand_name": "Selkirk", "model_name": "Power Air", "price_brl": "1500.00", "product_url": "https://example.com/p1", "image_url": ""}]
        result = ingest_rows(rows, store_id=1, session=session)
        assert result["updated"] == 1
        assert result["created"] == 0
        assert existing_offer.price_brl == Decimal("1500.00")

    def test_empty_rows(self):
        session = self._make_mock_session()
        result = ingest_rows([], store_id=1, session=session)
        assert result == {"created": 0, "updated": 0, "skipped": 0}
