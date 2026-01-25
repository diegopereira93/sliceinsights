"""
Shared test fixtures for PickleMatch Advisor tests.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4
from decimal import Decimal

from app.main import app
from app.db.database import get_session


class MockPaddle:
    """Mock paddle for testing."""
    def __init__(self, id=None, name="Test Paddle", brand_name="Test Brand",
                 power=7.0, control=7.0, spin=7.0, sweet_spot=7.0):
        self.id = id or uuid4()
        self.model_name = name
        self.search_keywords = ["test", "paddle"]
        self.power_rating = power
        self.control_rating = control
        self.spin_rating = spin
        self.sweet_spot_rating = sweet_spot
        self.twist_weight = 6.5
        self.core_material = "Honeycomb Polymer"
        self.core_thickness_mm = 16.0
        self.swing_weight = 115
        self.spin_rpm = 2200
        self.power_original = 8.5
        self.handle_length = "5.5"
        self.grip_circumference = "4.25"
        self.weight_avg_g = 220.0
        self.ideal_for_tennis_elbow = False
        self.is_featured = False
        self.available_in_brazil = True
        self.image_url = None
        
        from app.models.enums import FaceMaterial, PaddleShape, SkillLevel
        self.face_material = FaceMaterial.CARBON
        self.shape = PaddleShape.ELONGATED
        self.skill_level = SkillLevel.INTERMEDIATE
        
        # Brand
        self.brand = MagicMock()
        self.brand.id = 1
        self.brand.name = brand_name
        self.brand.website = "https://test.com"
        self.brand_id = 1


class MockBrand:
    """Mock brand for testing."""
    def __init__(self, id=1, name="Test Brand"):
        self.id = id
        self.name = name
        self.website = "https://test.com"


class MockMarketOffer:
    """Mock market offer for testing."""
    def __init__(self, paddle_id, price=1000.0):
        self.id = uuid4()
        self.paddle_id = paddle_id
        self.price_brl = Decimal(str(price))
        self.store_name = "Test Store"
        self.url = "https://store.test.com"
        self.is_active = True
        from datetime import datetime
        self.last_updated = datetime.now()


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    return AsyncMock()


@pytest.fixture
def mock_paddle():
    """Create a mock paddle."""
    return MockPaddle()


@pytest.fixture
def mock_brand():
    """Create a mock brand."""
    return MockBrand()


@pytest_asyncio.fixture
async def async_client():
    """Create an async test client."""
    async def override_get_session():
        mock = AsyncMock()
        yield mock
    
    app.dependency_overrides[get_session] = override_get_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_recommendation_request():
    """Sample recommendation request body."""
    return {
        "skill_level": "intermediate",
        "budget_max_brl": 2000.0,
        "play_style": "balanced",
        "has_tennis_elbow": False,
        "limit": 5
    }
