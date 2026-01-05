"""
API tests for paddle endpoints.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.main import app
from app.db.database import get_session


@pytest.mark.asyncio
async def test_health_check_healthy():
    """Test health check returns healthy status."""
    async def mock_session_gen():
        mock = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = 1
        mock.exec.return_value = mock_result
        yield mock
    
    app.dependency_overrides[get_session] = mock_session_gen
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_check_db_unavailable():
    """Test health check returns 503 when DB is unavailable."""
    async def mock_session_gen():
        mock = AsyncMock()
        mock.exec.side_effect = Exception("DB connection failed")
        yield mock
    
    app.dependency_overrides[get_session] = mock_session_gen
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_brands():
    """Test listing brands returns proper format."""
    from tests.conftest import MockBrand
    
    mock_brands = [MockBrand(id=1, name="Joola"), MockBrand(id=2, name="Selkirk")]
    
    async def mock_session_gen():
        mock = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = mock_brands
        mock.exec.return_value = mock_result
        yield mock
    
    app.dependency_overrides[get_session] = mock_session_gen
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/brands")
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_paddles_pagination():
    """Test paddle listing respects pagination params."""
    from tests.conftest import MockPaddle
    from decimal import Decimal
    
    mock_paddles = [MockPaddle(name=f"Paddle {i}") for i in range(5)]
    
    async def mock_session_gen():
        mock = AsyncMock()
        
        # Mock for SELECT PaddleMaster
        paddles_result = MagicMock()
        paddles_result.all.return_value = mock_paddles
        
        # Mock for price aggregation
        price_result = MagicMock()
        price_result.first.return_value = Decimal("999.00")
        
        # Mock for count
        count_result = MagicMock()
        count_result.first.return_value = 5
        
        mock.exec.side_effect = [paddles_result] + [price_result, count_result] * 5 + [count_result]
        yield mock
    
    app.dependency_overrides[get_session] = mock_session_gen
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/paddles?limit=5&offset=0")
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "limit" in data
    assert "offset" in data
    assert data["limit"] == 5
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_get_paddle_not_found():
    """Test getting non-existent paddle returns 404."""
    fake_uuid = str(uuid4())
    
    async def mock_session_gen():
        mock = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock.exec.return_value = mock_result
        yield mock
    
    app.dependency_overrides[get_session] = mock_session_gen
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/paddles/{fake_uuid}")
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_search_requires_min_length():
    """Test search requires minimum query length."""
    async def mock_session_gen():
        yield AsyncMock()
    
    app.dependency_overrides[get_session] = mock_session_gen
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/search?q=a")  # Too short
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 422  # Validation error
