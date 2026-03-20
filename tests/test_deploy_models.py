"""
TDD RED phase: Tests for DeployLog model, version_id columns on MarketOffer and PaddleMaster.
These tests MUST FAIL before implementation and PASS after.
"""
import pytest


def test_deploy_log_model_instantiation():
    """Test 1: DeployLog model instantiation with all required fields."""
    from app.models.deploy_log import DeployLog
    d = DeployLog(
        batch_id="batch_20260319_2f4a8",
        version_id=1,
        status="pending",
        scrapers_passed=5,
    )
    assert d.batch_id == "batch_20260319_2f4a8"
    assert d.version_id == 1
    assert d.status == "pending"
    assert d.scrapers_passed == 5
    assert d.products_published == 0
    assert d.scrapers_total == 11
    assert d.failure_reason is None


def test_deploy_log_status_values():
    """Test 2: DeployLog.status accepts all valid values."""
    from app.models.deploy_log import DeployLog
    for status in ["pending", "validated", "published", "failed", "rolled_back"]:
        d = DeployLog(batch_id="b", version_id=1, status=status, scrapers_passed=0)
        assert d.status == status


def test_deploy_log_forced_defaults_false():
    """Test 3: DeployLog.forced defaults to False."""
    from app.models.deploy_log import DeployLog
    d = DeployLog(batch_id="b", version_id=1, status="pending", scrapers_passed=0)
    assert d.forced is False


def test_market_offer_has_version_id():
    """Test 4: MarketOffer model has version_id field (Optional[int], default None)."""
    from app.models.market_offer import MarketOffer
    assert hasattr(MarketOffer, "version_id"), "MarketOffer missing version_id field"
    # Verify it's accessible and defaults to None
    import uuid
    offer = MarketOffer(
        store_name="TestStore",
        price_brl=100.0,
        url="https://example.com",
        paddle_id=uuid.uuid4(),
    )
    assert offer.version_id is None


def test_paddle_master_has_version_id():
    """Test 5: PaddleMaster model has version_id field (Optional[int], default None)."""
    from app.models.paddle import PaddleMaster
    assert hasattr(PaddleMaster, "version_id"), "PaddleMaster missing version_id field"
    paddle = PaddleMaster(
        model_name="Test Paddle",
        brand_id=1,
    )
    assert paddle.version_id is None
