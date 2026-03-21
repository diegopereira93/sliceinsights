"""
Unit tests for scraper modules.

All tests are fully mocked — no network calls are made, no database required.
Follows the same patterns as tests/test_fetchers.py.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.scraper_utils import (
    parse_brand_model,
    shopify_product_to_row,
    fetch_shopify_products,
    fetch_html_products,
)


# ═══════════════════════════════════════════════════════════════════════════════
# scraper_utils.py — parse_brand_model
# ═══════════════════════════════════════════════════════════════════════════════

class TestParseBrandModel:
    """Tests for parse_brand_model() — brand/model extraction from product titles."""

    def test_known_brand_extracted_at_start(self):
        brand, model = parse_brand_model("Joola Perseus 16mm")
        assert brand == "Joola"
        assert "Perseus" in model

    def test_known_brand_case_insensitive(self):
        brand, model = parse_brand_model("joola Perseus 16mm")
        assert brand == "Joola"

    def test_strips_mm_suffix_from_model(self):
        brand, model = parse_brand_model("Selkirk Luxx Control Air 16mm")
        assert "16mm" not in model

    def test_strips_raquete_de_pickleball_prefix(self):
        brand, model = parse_brand_model("Raquete de Pickleball Joola Ben Johns")
        assert brand == "Joola"

    def test_strips_paddle_prefix(self):
        brand, model = parse_brand_model("Paddle Selkirk Luxx Control")
        assert brand == "Selkirk"

    def test_unknown_brand_falls_back_to_first_word(self):
        brand, model = parse_brand_model("UnknownBrand Super Model Pro")
        assert brand == "Unknownbrand"
        assert "Super" in model

    def test_known_brand_six_zero_multi_word(self):
        brand, model = parse_brand_model("Six Zero Double Black Diamond")
        assert brand == "Six Zero"
        assert "Double Black Diamond" in model

    def test_bread_and_butter_brand(self):
        brand, model = parse_brand_model("Bread & Butter Filth")
        assert brand == "Bread & Butter"
        assert "Filth" in model

    def test_returns_tuple_of_two_strings(self):
        result = parse_brand_model("Engage Pursuit EX 6.0")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)


# ═══════════════════════════════════════════════════════════════════════════════
# scraper_utils.py — shopify_product_to_row
# ═══════════════════════════════════════════════════════════════════════════════

class TestShopifyProductToRow:
    """Tests for shopify_product_to_row() — Shopify JSON → output dict."""

    def _make_product(self, available=True, price="1299.00", images=True):
        return {
            "title": "Joola Perseus 16mm",
            "handle": "joola-perseus-16mm",
            "variants": [
                {"available": available, "price": price}
            ],
            "images": [{"src": "https://cdn.example.com/joola.jpg"}] if images else [],
        }

    def test_returns_dict_for_available_product(self):
        row = shopify_product_to_row(
            self._make_product(), "yosports.com.br", "yoSports", "Joola", "Perseus 16mm"
        )
        assert row is not None
        assert row["brand_name"] == "Joola"
        assert row["model_name"] == "Perseus 16mm"
        assert row["price_brl"] == 1299.0
        assert row["store_name"] == "yoSports"
        assert "yosports.com.br" in row["product_url"]

    def test_returns_none_when_no_available_variants(self):
        row = shopify_product_to_row(
            self._make_product(available=False),
            "yosports.com.br", "yoSports", "Joola", "Perseus 16mm"
        )
        assert row is None

    def test_picks_minimum_price_across_variants(self):
        product = {
            "title": "Joola Perseus",
            "handle": "joola-perseus",
            "variants": [
                {"available": True, "price": "1500.00"},
                {"available": True, "price": "1200.00"},
                {"available": True, "price": "1800.00"},
            ],
            "images": [],
        }
        row = shopify_product_to_row(product, "example.com", "TestStore", "Joola", "Perseus")
        assert row["price_brl"] == 1200.0

    def test_image_url_empty_when_no_images(self):
        row = shopify_product_to_row(
            self._make_product(images=False),
            "yosports.com.br", "yoSports", "Joola", "Perseus 16mm"
        )
        assert row is not None
        assert row["image_url"] == ""

    def test_product_url_uses_handle(self):
        row = shopify_product_to_row(
            self._make_product(), "yosports.com.br", "yoSports", "Joola", "Perseus 16mm"
        )
        assert "joola-perseus-16mm" in row["product_url"]

    def test_output_has_all_required_keys(self):
        row = shopify_product_to_row(
            self._make_product(), "yosports.com.br", "yoSports", "Joola", "Perseus 16mm"
        )
        required = {"brand_name", "model_name", "price_brl", "product_url", "store_name", "image_url"}
        assert required == set(row.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# scraper_utils.py — fetch_shopify_products (mocked HTTP)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFetchShopifyProducts:
    """Tests for fetch_shopify_products() with all network calls mocked."""

    def _make_response(self, products, status=200):
        mock = MagicMock()
        mock.status_code = status
        mock.json.return_value = {"products": products}
        return mock

    @patch("scripts.scraper_utils.requests.get")
    @patch("scripts.scraper_utils.time.sleep")  # avoid actual delays
    def test_returns_matching_products(self, mock_sleep, mock_get):
        products = [
            {"title": "Joola Perseus", "tags": ["pickleball"], "product_type": "paddle"},
            {"title": "Joola Perseus", "tags": ["pickleball"], "product_type": "paddle"},
        ]
        # First call: returns products. Second call: empty (stop pagination).
        mock_get.side_effect = [
            self._make_response(products),
            self._make_response([]),
        ]
        result = fetch_shopify_products("yosports.com.br", ["pickleball"])
        assert len(result) == 2

    @patch("scripts.scraper_utils.requests.get")
    @patch("scripts.scraper_utils.time.sleep")
    def test_filters_out_non_matching_products(self, mock_sleep, mock_get):
        products = [
            {"title": "Beach Tennis Racket", "tags": ["beach-tennis"], "product_type": "racket"},
            {"title": "Joola Perseus", "tags": ["pickleball"], "product_type": "paddle"},
        ]
        mock_get.side_effect = [
            self._make_response(products),
            self._make_response([]),
        ]
        result = fetch_shopify_products("example.com", ["pickleball"])
        assert len(result) == 1
        assert result[0]["title"] == "Joola Perseus"

    @patch("scripts.scraper_utils.requests.get")
    @patch("scripts.scraper_utils.time.sleep")
    def test_stops_on_non_200_response(self, mock_sleep, mock_get):
        mock_get.return_value = self._make_response([], status=429)
        result = fetch_shopify_products("example.com", ["pickleball"])
        assert result == []
        assert mock_get.call_count == 1

    @patch("scripts.scraper_utils.requests.get")
    @patch("scripts.scraper_utils.time.sleep")
    def test_paginates_until_empty_page(self, mock_sleep, mock_get):
        page1 = [{"title": "Joola Perseus", "tags": ["pickleball"], "product_type": "paddle"}]
        page2 = [{"title": "Selkirk Luxx", "tags": ["pickleball"], "product_type": "paddle"}]
        mock_get.side_effect = [
            self._make_response(page1),
            self._make_response(page2),
            self._make_response([]),
        ]
        result = fetch_shopify_products("example.com", ["pickleball"])
        assert len(result) == 2
        assert mock_get.call_count == 3


# ═══════════════════════════════════════════════════════════════════════════════
# scraper_utils.py — fetch_html_products (mocked HTTP + BeautifulSoup)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFetchHtmlProducts:
    """Tests for fetch_html_products() — generic HTML scraper."""

    SELECTORS = {
        "container": "li.product",
        "title": "h2",
        "price": ".price",
        "link": "a",
        "image": "img",
    }

    @patch("scripts.scraper_utils.requests.get")
    @patch("scripts.scraper_utils.time.sleep")
    def test_stops_on_non_200_status(self, mock_sleep, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp
        result = fetch_html_products("example.com", "pickleball", self.SELECTORS, "TestStore")
        assert result == []

    @patch("scripts.scraper_utils.requests.get")
    @patch("scripts.scraper_utils.time.sleep")
    def test_stops_on_request_exception(self, mock_sleep, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        result = fetch_html_products("example.com", "pickleball", self.SELECTORS, "TestStore")
        assert result == []

    @patch("scripts.scraper_utils.requests.get")
    @patch("scripts.scraper_utils.time.sleep")
    def test_parses_product_cards_from_html(self, mock_sleep, mock_get):
        html = """
        <html><body>
          <ul>
            <li class="product">
              <h2>Joola Perseus 16mm</h2>
              <span class="price">R$ 1.299,00</span>
              <a href="/products/joola-perseus">Ver produto</a>
              <img src="https://cdn.example.com/joola.jpg" />
            </li>
          </ul>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html
        # First call: page 1 with a product. Second call: empty page (stops loop).
        empty_resp = MagicMock()
        empty_resp.status_code = 200
        empty_resp.text = "<html><body></body></html>"
        mock_get.side_effect = [mock_resp, empty_resp]

        result = fetch_html_products("example.com", "pickleball", self.SELECTORS, "TestStore")
        assert len(result) == 1
        assert result[0]["brand_name"] == "Joola"
        assert result[0]["price_brl"] == 1299.0
        assert result[0]["store_name"] == "TestStore"

    @patch("scripts.scraper_utils.requests.get")
    @patch("scripts.scraper_utils.time.sleep")
    def test_skips_cards_with_zero_price(self, mock_sleep, mock_get):
        html = """
        <html><body>
          <ul>
            <li class="product">
              <h2>Joola Perseus</h2>
              <span class="price">Consulte</span>
              <a href="/products/joola">Ver</a>
              <img src="img.jpg" />
            </li>
          </ul>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html
        empty_resp = MagicMock()
        empty_resp.status_code = 200
        empty_resp.text = "<html><body></body></html>"
        mock_get.side_effect = [mock_resp, empty_resp]

        result = fetch_html_products("example.com", "pickleball", self.SELECTORS, "TestStore")
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# scrape_yosports.py — main() with all external calls mocked
# ═══════════════════════════════════════════════════════════════════════════════

class TestScrapeYoSportsMain:
    """Tests for scrape_yosports.main() with all I/O fully mocked."""

    def _make_product(self, title="Joola Perseus 16mm", tags=None):
        return {
            "title": title,
            "handle": title.lower().replace(" ", "-"),
            "tags": tags or ["pickleball"],
            "product_type": "paddle",
            "variants": [{"available": True, "price": "1299.00"}],
            "images": [{"src": "https://cdn.example.com/img.jpg"}],
        }

    @patch("scripts.scrape_yosports.ingest_rows", return_value={"created": 1, "updated": 0, "skipped": 0})
    @patch("scripts.scrape_yosports.init_db_sync")
    @patch("scripts.scrape_yosports.Session")
    @patch("scripts.scraper_utils.time.sleep")
    @patch("scripts.scraper_utils.requests.get")
    def test_main_filters_accessories(self, mock_get, mock_sleep, mock_session_cls, mock_init, mock_ingest):
        import scripts.scrape_yosports as yosports
        products = [
            self._make_product("Joola Perseus 16mm", tags=["pickleball"]),
            self._make_product("Bolinha Dura", tags=["pickleball", "bola"]),
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"products": products}
        empty_resp = MagicMock()
        empty_resp.status_code = 200
        empty_resp.json.return_value = {"products": []}
        mock_get.side_effect = [mock_resp, empty_resp]

        mock_store = MagicMock()
        mock_store.id = 1
        mock_session = MagicMock()
        mock_session.exec.return_value.one.return_value = mock_store
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        yosports.main()
        mock_ingest.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("scripts.scrape_yosports.ingest_rows", return_value={"created": 1, "updated": 0, "skipped": 0})
    @patch("scripts.scrape_yosports.init_db_sync")
    @patch("scripts.scrape_yosports.Session")
    @patch("scripts.scraper_utils.time.sleep")
    @patch("scripts.scraper_utils.requests.get")
    def test_main_skips_beach_tennis_rackets(self, mock_get, mock_sleep, mock_session_cls, mock_init, mock_ingest):
        import scripts.scrape_yosports as yosports
        products = [
            self._make_product("Raquete de Beach Tennis Head", tags=["beach-tennis"]),
            self._make_product("Joola Perseus", tags=["pickleball"]),
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"products": products}
        empty_resp = MagicMock()
        empty_resp.status_code = 200
        empty_resp.json.return_value = {"products": []}
        mock_get.side_effect = [mock_resp, empty_resp]

        mock_store = MagicMock()
        mock_store.id = 1
        mock_session = MagicMock()
        mock_session.exec.return_value.one.return_value = mock_store
        mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)

        yosports.main()
        mock_ingest.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# scrape_justpaddles.py — unit tests for individual async functions
# ═══════════════════════════════════════════════════════════════════════════════

class TestScrapeJustPaddlesExtractLabData:
    """Tests for extract_lab_data() — DOM extraction function."""

    def test_extract_lab_data_returns_empty_when_no_lab_section(self):
        import asyncio
        from scripts.scrape_justpaddles import extract_lab_data

        async def run():
            mock_page = MagicMock()
            mock_page.query_selector = MagicMock(return_value=None)
            # Make it return None for 'Paddle Lab' lookup (awaitable)
            async def fake_query_selector(selector):
                return None
            mock_page.query_selector = fake_query_selector
            return await extract_lab_data(mock_page)

        result = asyncio.run(run())
        assert result == {}

    def test_extract_lab_data_returns_swing_and_twist_weight(self):
        import asyncio
        from scripts.scrape_justpaddles import extract_lab_data

        async def run():
            mock_page = MagicMock()

            swing_elem = MagicMock()
            twist_elem = MagicMock()

            async def fake_query_selector(selector):
                if "Paddle Lab" in selector:
                    return MagicMock()  # lab section found
                if "Swing Weight" in selector:
                    return swing_elem
                if "Twist Weight" in selector:
                    return twist_elem
                return None

            async def swing_inner_text():
                return "116"

            async def twist_inner_text():
                return "6.1"

            swing_elem.inner_text = swing_inner_text
            twist_elem.inner_text = twist_inner_text
            mock_page.query_selector = fake_query_selector
            mock_page.url = "https://www.justpaddles.com/products/joola-perseus"

            return await extract_lab_data(mock_page)

        result = asyncio.run(run())
        assert result.get("swing_weight") == 116
        assert result.get("twist_weight") == 6.1


# ═══════════════════════════════════════════════════════════════════════════════
# Scraper module importability checks
# ═══════════════════════════════════════════════════════════════════════════════

class TestScraperImports:
    """Verify all scraper modules can be imported without side effects."""

    def test_scraper_utils_imports(self):
        import scripts.scraper_utils
        assert scripts.scraper_utils is not None

    def test_scrape_yosports_imports(self):
        import scripts.scrape_yosports
        assert scripts.scrape_yosports is not None

    def test_scrape_brazil_store_imports(self):
        import scripts.scrape_brazil_store
        assert scripts.scrape_brazil_store is not None

    def test_scrape_joola_imports(self):
        import scripts.scrape_joola
        assert scripts.scrape_joola is not None

    def test_scrape_propadel_imports(self):
        import scripts.scrape_propadel
        assert scripts.scrape_propadel is not None
