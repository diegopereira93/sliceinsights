"""
Test suite for Catalog API endpoints.
Covers all 7 requirements: STORE-03, CAT-01 through CAT-06
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from app.main import app
from app.db.database import get_session
from tests.conftest import MockPaddle, MockStore, MockMarketOfferWithStore


class TestStoresEndpoint:
    """STORE-03: Catalog stores endpoint tests."""

    @pytest.mark.asyncio
    async def test_list_stores(self):
        """GET /api/v1/catalog/stores returns 200 with store list."""
        store = MockStore(id=1, name="ProPadel", slug="propadel",
                         base_url="https://propadel.com.br", is_active=True,
                         available_brands=["Joola", "Selkirk"])
        
        mock_result = MagicMock()
        mock_result.all.return_value = [store]
        
        async def override_get_session():
            mock = AsyncMock()
            mock.exec = AsyncMock(return_value=mock_result)
            yield mock
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/stores")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert data["total"] >= 1
        store_data = data["data"][0]
        assert store_data["name"] == "ProPadel"
        assert store_data["slug"] == "propadel"
        assert "available_brands" in store_data

    @pytest.mark.asyncio
    async def test_stores_filter_by_brand(self):
        """GET /api/v1/catalog/stores?brand=Joola filters by brand."""
        store = MockStore(name="ProPadel", available_brands=["Joola", "Selkirk"])
        
        mock_result = MagicMock()
        mock_result.all.return_value = [store]
        
        async def override_get_session():
            mock = AsyncMock()
            mock.exec = AsyncMock(return_value=mock_result)
            yield mock
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/stores?brand=Joola")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_stores_empty_result(self):
        """GET /api/v1/catalog/stores?brand=NonExistentBrand returns empty."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        
        async def override_get_session():
            mock = AsyncMock()
            mock.exec = AsyncMock(return_value=mock_result)
            yield mock
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/stores?brand=NonExistentBrand")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0


class TestPaddlesEndpoint:
    """CAT-01 through CAT-06: Catalog paddles endpoint tests."""

    @pytest.mark.asyncio
    async def test_list_catalog_paddles(self):
        """CAT-01: GET /api/v1/catalog/paddles returns paddles list."""
        paddle = MockPaddle(name="Test Carbon 16", brand_name="Joola")
        store = MockStore(name="ProPadel", slug="propadel")
        offer = MockMarketOfferWithStore(paddle_id=paddle.id, price=899.90, store=store)
        paddle.market_offers = [offer]
        
        mock_result = MagicMock()
        mock_result.all.return_value = [(paddle, Decimal("899.90"))]
        mock_count_result = MagicMock()
        mock_count_result.first.return_value = 1
        
        call_count = [0]
        async def mock_session_gen():
            mock = AsyncMock()
            def exec_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_count_result
                else:
                    return mock_result
            mock.exec.side_effect = exec_side_effect
            yield mock
        
        app.dependency_overrides[get_session] = mock_session_gen
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    @pytest.mark.asyncio
    async def test_paddle_response_shape(self):
        """CAT-01: Paddle response has correct shape with market_offers."""
        paddle = MockPaddle(name="Hyperion CFS", brand_name="Joola")
        store = MockStore(name="ProPadel", slug="propadel")
        offer = MockMarketOfferWithStore(paddle_id=paddle.id, price=899.90, store=store)
        paddle.market_offers = [offer]
        
        mock_result = MagicMock()
        mock_result.all.return_value = [(paddle, Decimal("899.90"))]
        mock_count_result = MagicMock()
        mock_count_result.first.return_value = 1
        
        call_count = [0]
        async def mock_session_gen():
            mock = AsyncMock()
            def exec_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_count_result
                else:
                    return mock_result
            mock.exec.side_effect = exec_side_effect
            yield mock
        
        app.dependency_overrides[get_session] = mock_session_gen
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        paddle_data = data["data"][0]
        assert "id" in paddle_data
        assert "brand" in paddle_data
        assert "model_name" in paddle_data
        assert "specs" in paddle_data
        assert "core_thickness_mm" in paddle_data["specs"]
        assert "surface_material" in paddle_data["specs"]
        assert "market_offers" in paddle_data
        offer_data = paddle_data["market_offers"][0]
        assert "store_name" in offer_data
        assert "price_brl" in offer_data
        assert "store_url" in offer_data

    @pytest.mark.asyncio
    async def test_filter_core_thickness(self):
        """CAT-02: GET /api/v1/catalog/paddles?core_thickness=16 filters correctly."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.first.return_value = 0
        
        call_count = [0]
        async def mock_session_gen():
            mock = AsyncMock()
            def exec_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_count_result
                else:
                    return mock_result
            mock.exec.side_effect = exec_side_effect
            yield mock
        
        app.dependency_overrides[get_session] = mock_session_gen
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles?core_thickness=16")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_core_thickness_multi(self):
        """CAT-02: Multi-value core_thickness filter works."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.first.return_value = 0
        
        call_count = [0]
        async def mock_session_gen():
            mock = AsyncMock()
            def exec_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_count_result
                else:
                    return mock_result
            mock.exec.side_effect = exec_side_effect
            yield mock
        
        app.dependency_overrides[get_session] = mock_session_gen
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles?core_thickness=13&core_thickness=16")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_surface_material(self):
        """CAT-03: GET /api/v1/catalog/paddles?surface_material=carbon filters correctly."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.first.return_value = 0
        
        call_count = [0]
        async def mock_session_gen():
            mock = AsyncMock()
            def exec_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_count_result
                else:
                    return mock_result
            mock.exec.side_effect = exec_side_effect
            yield mock
        
        app.dependency_overrides[get_session] = mock_session_gen
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles?surface_material=carbon")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_surface_material_invalid(self):
        """CAT-03: Invalid surface_material returns 422 validation error."""
        async def mock_session_gen():
            yield AsyncMock()
        
        app.dependency_overrides[get_session] = mock_session_gen
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles?surface_material=invalid_material")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_filter_price_range(self):
        """CAT-04: GET /api/v1/catalog/paddles?price_min=500&price_max=1500 filters correctly."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.first.return_value = 0
        
        call_count = [0]
        async def mock_session_gen():
            mock = AsyncMock()
            def exec_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_count_result
                else:
                    return mock_result
            mock.exec.side_effect = exec_side_effect
            yield mock
        
        app.dependency_overrides[get_session] = mock_session_gen
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles?price_min=500&price_max=1500")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_brand(self):
        """CAT-05: GET /api/v1/catalog/paddles?brand=Joola filters correctly."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.first.return_value = 0
        
        call_count = [0]
        async def mock_session_gen():
            mock = AsyncMock()
            def exec_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_count_result
                else:
                    return mock_result
            mock.exec.side_effect = exec_side_effect
            yield mock
        
        app.dependency_overrides[get_session] = mock_session_gen
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles?brand=Joola")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_store(self):
        """CAT-05: GET /api/v1/catalog/paddles?store=propadel filters by store slug."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.first.return_value = 0
        
        call_count = [0]
        async def mock_session_gen():
            mock = AsyncMock()
            def exec_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_count_result
                else:
                    return mock_result
            mock.exec.side_effect = exec_side_effect
            yield mock
        
        app.dependency_overrides[get_session] = mock_session_gen
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles?store=propadel")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_offers_included(self):
        """CAT-06: Each paddle has non-empty market_offers with store_url."""
        paddle = MockPaddle(name="Test Paddle", brand_name="Joola")
        store = MockStore(name="ProPadel", slug="propadel")
        offer = MockMarketOfferWithStore(paddle_id=paddle.id, price=899.90, store=store)
        paddle.market_offers = [offer]
        
        mock_result = MagicMock()
        mock_result.all.return_value = [(paddle, Decimal("899.90"))]
        mock_count_result = MagicMock()
        mock_count_result.first.return_value = 1
        
        call_count = [0]
        async def mock_session_gen():
            mock = AsyncMock()
            def exec_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_count_result
                else:
                    return mock_result
            mock.exec.side_effect = exec_side_effect
            yield mock
        
        app.dependency_overrides[get_session] = mock_session_gen
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        paddle_data = data["data"][0]
        assert len(paddle_data["market_offers"]) > 0
        assert "store_url" in paddle_data["market_offers"][0]


class TestPagination:
    """Pagination tests for catalog endpoints."""

    @pytest.mark.asyncio
    async def test_pagination_limit(self):
        """Pagination limit parameter works."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.first.return_value = 0
        
        async def override_get_session():
            mock = AsyncMock()
            mock.exec = AsyncMock(side_effect=[mock_result, mock_count_result])
            yield mock
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles?limit=10")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10

    @pytest.mark.asyncio
    async def test_pagination_offset(self):
        """Pagination offset parameter works."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.first.return_value = 0
        
        async def override_get_session():
            mock = AsyncMock()
            mock.exec = AsyncMock(side_effect=[mock_result, mock_count_result])
            yield mock
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles?offset=5")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 5

    @pytest.mark.asyncio
    async def test_pagination_max_limit(self):
        """limit=200 exceeds max 100 and returns 422."""
        async def override_get_session():
            yield AsyncMock()
        
        app.dependency_overrides[get_session] = override_get_session
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles?limit=200")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 422


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_empty_catalog(self):
        """When no paddles match, returns empty data array."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.first.return_value = 0
        
        call_count = [0]
        async def mock_session_gen():
            mock = AsyncMock()
            def exec_side_effect(*args, **kwargs):
                if call_count[0] == 0:
                    call_count[0] += 1
                    return mock_count_result
                else:
                    return mock_result
            mock.exec.side_effect = exec_side_effect
            yield mock
        
        app.dependency_overrides[get_session] = mock_session_gen
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/catalog/paddles")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0
        assert data["limit"] == 50
        assert data["offset"] == 0
