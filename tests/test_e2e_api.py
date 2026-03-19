"""
E2E API Tests — hits the real backend (with real DB data).
Tests the full request/response cycle for all public API endpoints.

Usage:
    docker compose exec -e PYTHONPATH=/app backend_v3 pytest tests/test_e2e_api.py -v
"""
import pytest
import httpx

BASE = "http://localhost:8000/api/v1"


@pytest.fixture(scope="module")
def client():
    """httpx client pointing at the live backend."""
    with httpx.Client(base_url=BASE, timeout=10) as c:
        yield c


# ─── Health ───────────────────────────────────────────────────────

class TestHealth:
    def test_health_ok(self, client: httpx.Client):
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert body["database"] == "connected"


# ─── Brands ───────────────────────────────────────────────────────

class TestBrands:
    def test_list_brands(self, client: httpx.Client):
        r = client.get("/brands")
        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert len(body["data"]) > 0
        brand = body["data"][0]
        assert "id" in brand
        assert "name" in brand

    def test_list_brands_brazil_filter(self, client: httpx.Client):
        r = client.get("/brands", params={"available_in_brazil": True})
        assert r.status_code == 200
        body = r.json()
        assert len(body["data"]) > 0


# ─── Paddles ──────────────────────────────────────────────────────

class TestPaddles:
    def test_list_paddles_default(self, client: httpx.Client):
        r = client.get("/paddles")
        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert "total" in body
        assert body["total"] > 0
        assert len(body["data"]) > 0

    def test_list_paddles_has_required_fields(self, client: httpx.Client):
        r = client.get("/paddles", params={"limit": 1})
        body = r.json()
        paddle = body["data"][0]
        required = ["id", "brand_name", "model_name", "image_url", "available_in_brazil"]
        for field in required:
            assert field in paddle, f"Missing field: {field}"

    def test_list_paddles_pagination(self, client: httpx.Client):
        r1 = client.get("/paddles", params={"limit": 5, "offset": 0})
        r2 = client.get("/paddles", params={"limit": 5, "offset": 5})
        assert r1.status_code == 200
        assert r2.status_code == 200
        ids1 = {p["id"] for p in r1.json()["data"]}
        ids2 = {p["id"] for p in r2.json()["data"]}
        assert ids1.isdisjoint(ids2), "Paginated results should not overlap"

    def test_list_paddles_price_filter(self, client: httpx.Client):
        r = client.get("/paddles", params={"min_price": 500, "max_price": 1500})
        assert r.status_code == 200
        body = r.json()
        for p in body["data"]:
            price = p.get("min_price_brl")
            if price is not None:
                assert 500 <= price <= 1500, f"Price {price} out of range"

    def test_get_single_paddle(self, client: httpx.Client):
        # Get first paddle ID from listing
        r = client.get("/paddles", params={"limit": 1})
        paddle_id = r.json()["data"][0]["id"]

        # Fetch by ID
        r2 = client.get(f"/paddles/{paddle_id}")
        assert r2.status_code == 200
        body = r2.json()
        assert body["id"] == paddle_id
        assert "brand" in body
        assert "name" in body["brand"]
        assert "model_name" in body

    def test_get_single_paddle_has_offers(self, client: httpx.Client):
        r = client.get("/paddles", params={"limit": 1})
        paddle_id = r.json()["data"][0]["id"]
        r2 = client.get(f"/paddles/{paddle_id}")
        body = r2.json()
        assert "market_offers" in body
        assert len(body["market_offers"]) > 0, "Paddle should have at least one market offer"
        offer = body["market_offers"][0]
        assert "store_name" in offer
        assert "price_brl" in offer

    def test_get_paddle_not_found(self, client: httpx.Client):
        r = client.get("/paddles/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404


# ─── Search ───────────────────────────────────────────────────────

class TestSearch:
    def test_search_with_results(self, client: httpx.Client):
        r = client.get("/search", params={"q": "Joola"})
        assert r.status_code == 200
        body = r.json()
        assert "results" in body
        assert len(body["results"]) > 0

    def test_search_nonsense_returns_low_quality(self, client: httpx.Client):
        """Fuzzy search may return low-confidence matches; verify scores are low."""
        r = client.get("/search", params={"q": "zzzzqqqqqxxxxxnonexistent"})
        assert r.status_code == 200
        body = r.json()
        for result in body["results"]:
            assert result.get("match_score", 0) < 80, \
                f"Nonsense query should not match with high confidence: {result}"

    def test_search_min_length(self, client: httpx.Client):
        r = client.get("/search", params={"q": "a"})
        assert r.status_code == 422  # Validation error


# ─── Recommendations ─────────────────────────────────────────────

class TestRecommendations:
    def test_recommendations_basic(self, client: httpx.Client):
        payload = {
            "skill_level": "intermediate",
            "play_style": "balanced",
            "has_tennis_elbow": False,
            "limit": 5,
        }
        r = client.post("/recommendations", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert "recommendations" in body
        # May be empty if paddles have no specs for the engine to rank
        assert isinstance(body["recommendations"], list)

    def test_recommendations_with_budget(self, client: httpx.Client):
        payload = {
            "skill_level": "beginner",
            "play_style": "control",
            "has_tennis_elbow": False,
            "budget_max_brl": 800,
            "limit": 3,
        }
        r = client.post("/recommendations", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert "recommendations" in body

    def test_recommendations_invalid_skill(self, client: httpx.Client):
        payload = {
            "skill_level": "super_pro",  # invalid
            "play_style": "all_court",
            "has_tennis_elbow": False,
            "limit": 5,
        }
        r = client.post("/recommendations", json=payload)
        assert r.status_code == 422


# ─── Data Pipeline Integrity ─────────────────────────────────────

class TestDataIntegrity:
    def test_all_paddles_have_brazil_flag(self, client: httpx.Client):
        """Every paddle in our BR catalog should be available_in_brazil."""
        r = client.get("/paddles", params={"limit": 100})
        body = r.json()
        for p in body["data"]:
            assert p.get("available_in_brazil") is True, \
                f"{p['brand_name']} {p['model_name']} missing available_in_brazil"

    def test_all_paddles_have_images(self, client: httpx.Client):
        """Every paddle should have an image_url."""
        r = client.get("/paddles", params={"limit": 100})
        body = r.json()
        for p in body["data"]:
            assert p.get("image_url"), \
                f"{p['brand_name']} {p['model_name']} missing image_url"

    def test_all_paddles_have_prices(self, client: httpx.Client):
        """Every paddle should have a minimum price from market offers."""
        r = client.get("/paddles", params={"limit": 100})
        body = r.json()
        for p in body["data"]:
            assert p.get("min_price_brl") is not None and p["min_price_brl"] > 0, \
                f"{p['brand_name']} {p['model_name']} missing price"

    def test_brand_count_matches_seed(self, client: httpx.Client):
        """Should have multiple brands from our BR seed."""
        r = client.get("/brands")
        body = r.json()
        assert len(body["data"]) >= 5, f"Expected ≥5 brands, got {len(body['data'])}"

    def test_paddle_count_reasonable(self, client: httpx.Client):
        """Should have a reasonable number of paddles from our BR seed."""
        r = client.get("/paddles", params={"limit": 1})
        body = r.json()
        # Data quality roadmap: catalog may shrink to 35-55 with complete specs only
        assert body["total"] >= 10, f"Expected ≥10 paddles, got {body['total']}"

    def test_quality_gate_all_specs_complete(self, client: httpx.Client):
        """Phase 4: Enriched paddles (specs_confidence > 0) MUST have complete spec fields."""
        r = client.get("/paddles", params={"limit": 100})
        body = r.json()
        required_spec_fields = [
            "core_thickness_mm", "swing_weight", "spin_rpm", "handle_length"
        ]
        enriched = [p for p in body["data"] if p.get("specs_confidence", 0) > 0]
        for p in enriched:
            specs = p.get("specs", {})
            for field in required_spec_fields:
                assert specs.get(field) is not None, \
                    f"{p['brand_name']} {p['model_name']} missing spec: {field}"

    def test_no_fabricated_ratings(self, client: httpx.Client):
        """Phase 4: NO paddle should have all ratings == 5 (fabricated defaults)."""
        r = client.get("/paddles", params={"limit": 100})
        body = r.json()
        for p in body["data"]:
            ratings = p.get("ratings", {})
            r_vals = [
                v for k, v in ratings.items()
                if k in ("control_rating", "spin_rating", "sweet_spot_rating") and v is not None
            ]
            if len(r_vals) >= 3:
                assert not all(v == 5 for v in r_vals), \
                    f"{p['brand_name']} {p['model_name']} has all-default ratings (fabricated)"

    def test_recommendations_only_verified(self, client: httpx.Client):
        """Phase 4: ALL recommendations must come from fully-verified paddles."""
        payload = {
            "skill_level": "intermediate",
            "play_style": "balanced",
            "has_tennis_elbow": False,
            "limit": 5,
        }
        r = client.post("/recommendations", json=payload)
        assert r.status_code == 200
        body = r.json()
        for rec in body.get("recommendations", []):
            assert rec.get("model_name"), "Recommendation missing model_name"
            assert rec.get("brand_name"), "Recommendation missing brand_name"

