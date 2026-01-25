"""
API tests for recommendation endpoints.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from uuid import uuid4

from app.main import app
from app.db.database import get_session


@pytest.mark.asyncio
async def test_recommendations_valid_request():
    """Test recommendations endpoint with valid request."""
    paddle_id = uuid4()
    from tests.conftest import MockPaddle
    mock_row = (
        MockPaddle(
            id=paddle_id,
            name="Test Paddle",
            power=7.0,
            control=7.0,
            spin=7.0,
            sweet_spot=7.0
        ),
        "Test Brand",
        Decimal("999.00"),
        2
    )
    
    async def mock_session_gen():
        mock = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock.exec.return_value = mock_result
        yield mock
    
    app.dependency_overrides[get_session] = mock_session_gen
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recommendations",
            json={
                "skill_level": "intermediate",
                "budget_max_brl": 2000.0,
                "play_style": "balanced",
                "has_tennis_elbow": False,
                "limit": 5
            }
        )
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "total_matching" in data


@pytest.mark.asyncio
async def test_recommendations_power_style():
    """Test recommendations with power play style."""
    paddle_id = uuid4()
    from tests.conftest import MockPaddle
    mock_row = (
        MockPaddle(
            id=paddle_id,
            name="Power Paddle",
            power=9.0,
            control=6.0,
            spin=7.0,
            sweet_spot=7.0
        ),
        "Power Brand",
        Decimal("1500.00"),
        1
    )
    
    async def mock_session_gen():
        mock = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock.exec.return_value = mock_result
        yield mock
    
    app.dependency_overrides[get_session] = mock_session_gen
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recommendations",
            json={
                "skill_level": "advanced",
                "budget_max_brl": 3000.0,
                "play_style": "power",
                "has_tennis_elbow": False,
                "limit": 10
            }
        )
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data


@pytest.mark.asyncio
async def test_recommendations_tennis_elbow():
    """Test recommendations filter for tennis elbow."""
    paddle_id = uuid4()
    from tests.conftest import MockPaddle
    mock_row = (
        MockPaddle(
            id=paddle_id,
            name="Elbow Friendly",
            power=6.0,
            control=8.0,
            spin=7.0,
            sweet_spot=9.0
        ),
        "Comfort Brand",
        Decimal("800.00"),
        3
    )
    mock_row[0].core_thickness_mm = 16.0
    
    async def mock_session_gen():
        mock = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock.exec.return_value = mock_result
        yield mock
    
    app.dependency_overrides[get_session] = mock_session_gen
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recommendations",
            json={
                "skill_level": "beginner",
                "budget_max_brl": 1000.0,
                "play_style": "control",
                "has_tennis_elbow": True,
                "limit": 5
            }
        )
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_recommendations_invalid_skill_level():
    """Test recommendations rejects invalid skill level."""
    async def mock_session_gen():
        yield AsyncMock()
    
    app.dependency_overrides[get_session] = mock_session_gen
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recommendations",
            json={
                "skill_level": "invalid_level",
                "budget_max_brl": 2000.0,
                "play_style": "balanced",
                "has_tennis_elbow": False
            }
        )
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_recommendations_missing_required_field():
    """Test recommendations requires skill_level."""
    async def mock_session_gen():
        yield AsyncMock()
    
    app.dependency_overrides[get_session] = mock_session_gen
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recommendations",
            json={
                "budget_max_brl": 2000.0,
                "play_style": "balanced"
            }
        )
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 422
