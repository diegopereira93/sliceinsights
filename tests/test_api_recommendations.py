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
from app.services.recommendation_engine import PlayStyle


@pytest.mark.asyncio
async def test_recommendations_valid_request():
    """Test recommendations endpoint with valid request."""
    paddle_id = uuid4()
    mock_row = (
        MagicMock(
            id=paddle_id,
            model_name="Test Paddle",
            power_rating=7.0,
            control_rating=7.0,
            spin_rating=7.0,
            sweet_spot_rating=7.0,
            twist_weight=6.5,
            ideal_for_tennis_elbow=False,
            skill_level=MagicMock(value="intermediate")
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
    assert "total_matched" in data


@pytest.mark.asyncio
async def test_recommendations_power_style():
    """Test recommendations with power play style."""
    paddle_id = uuid4()
    mock_row = (
        MagicMock(
            id=paddle_id,
            model_name="Power Paddle",
            power_rating=9.0,
            control_rating=6.0,
            spin_rating=7.0,
            sweet_spot_rating=7.0,
            twist_weight=5.5,
            ideal_for_tennis_elbow=False,
            skill_level=MagicMock(value="advanced")
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
    mock_row = (
        MagicMock(
            id=paddle_id,
            model_name="Elbow Friendly",
            power_rating=6.0,
            control_rating=8.0,
            spin_rating=7.0,
            sweet_spot_rating=9.0,
            twist_weight=7.5,
            ideal_for_tennis_elbow=True,
            skill_level=MagicMock(value="beginner")
        ),
        "Comfort Brand",
        Decimal("800.00"),
        3
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
