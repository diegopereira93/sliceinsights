"""
API tests for recommendation endpoints.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from uuid import uuid4

from app.main import app
from app.db.database import get_session
from app.schemas.user_profile import RecommendationResult, UserProfile
from app.models.enums import SkillLevel, PlayStyle


@pytest.mark.asyncio
async def test_recommend_valid_request():
    """Test /recommend endpoint with valid request."""
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
            "/api/v1/recommend",
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
async def test_recommend_market_offers_present():
    """Verify REC-02: market_offers field is present in recommendations."""
    paddle_id = uuid4()
    from tests.conftest import MockPaddle, MockStore, MockMarketOfferWithStore
    
    # Create paddle with market offers
    store = MockStore()
    paddle = MockPaddle(id=paddle_id, name="Test Paddle")
    offer = MockMarketOfferWithStore(paddle_id=paddle_id, price=999.0, store=store)
    paddle.market_offers = [offer]
    
    mock_row = (paddle, "Test Brand", Decimal("999.00"), 2)
    
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
            "/api/v1/recommend",
            json={
                "skill_level": "intermediate",
                "budget_max_brl": 2000.0,
                "play_style": "balanced",
                "has_tennis_elbow": False,
                "limit": 3
            }
        )
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    # Schema test - verify market_offers key exists in recommendation
    if data.get("recommendations"):
        assert "market_offers" in data["recommendations"][0]


@pytest.mark.asyncio
async def test_recommend_no_match_returns_dossier():
    """Verify REC-01: no-match returns recommendations:[] plus grok_dossier (not HTTP error)."""
    
    # Mock engine to return empty recommendations
    mock_result = RecommendationResult(
        user_profile=UserProfile(skill_level=SkillLevel.INTERMEDIATE, play_style=PlayStyle.BALANCED),
        recommendations=[],
        filters_applied={"budget_filter": True, "tennis_elbow_filter": False},
        total_matching=0,
        returned=0,
        grok_dossier=None,
    )
    
    async def mock_session_gen():
        mock = AsyncMock()
        mock_result_exec = MagicMock()
        mock_result_exec.all.return_value = []
        mock.exec.return_value = mock_result_exec
        yield mock
    
    app.dependency_overrides[get_session] = mock_session_gen
    
    with patch("app.api.endpoints.recommend.RecommendationEngine") as MockEngine:
        mock_engine_instance = AsyncMock()
        mock_engine_instance.get_recommendations.return_value = mock_result
        MockEngine.return_value = mock_engine_instance
        
        with patch("app.api.endpoints.recommend.llm_service.generate_dossier", new_callable=AsyncMock) as mock_dossier:
            mock_dossier.return_value = "No paddle found within budget."
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/recommend",
                    json={
                        "skill_level": "intermediate",
                        "budget_max_brl": 100.0,  # Very low budget to get no results
                        "play_style": "balanced",
                        "has_tennis_elbow": False,
                        "limit": 3
                    }
                )
    
    app.dependency_overrides.clear()
    
    # Should return 200 (NOT 404/500) with empty recommendations and dossier
    assert response.status_code == 200
    data = response.json()
    assert data["recommendations"] == []
    assert "grok_dossier" in data


@pytest.mark.asyncio
async def test_recommend_chat_endpoint():
    """Verify chat endpoint works correctly."""
    
    # Create mock messages
    messages = [{"role": "user", "content": "Qual a melhor?"}]
    context = "Raquete A specs..."
    
    with patch("app.api.endpoints.recommend.llm_service.chat_with_context", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "Test reply"
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/recommend/chat",
                json={
                    "messages": messages,
                    "context": context
                }
            )
    
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Test reply"


@pytest.mark.asyncio
async def test_recommend_chat_missing_context():
    """Verify chat endpoint validates required context field."""
    messages = [{"role": "user", "content": "Qual a melhor?"}]
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recommend/chat",
            json={
                "messages": messages
                # Missing context field
            }
        )
    
    assert response.status_code == 422  # Validation error


# Legacy tests updated from /recommendations to /recommend

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
            "/api/v1/recommend",
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
            "/api/v1/recommend",
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
            "/api/v1/recommend",
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
            "/api/v1/recommend",
            json={
                "budget_max_brl": 2000.0,
                "play_style": "balanced"
            }
        )
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 422