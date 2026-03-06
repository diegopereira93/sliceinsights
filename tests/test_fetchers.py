"""
Unit tests for the auto-fetch scripts.

Tests are fully mocked — no network calls are made.
"""
import io
import os
import base64
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.fetch_johnkew import (
    read_from_env_base64,
    download_with_playwright,
    download_file,
    convert_to_csv,
    main as fetch_johnkew_main,
)
from scripts.fetch_pb_studio import (
    blocks_to_dataframe,
    main as fetch_pbstudio_main,
)


# ═══════════════════════════════════════════════════════════════════════════════
# fetch_johnkew.py
# ═══════════════════════════════════════════════════════════════════════════════

def _make_xlsx_bytes() -> bytes:
    df = pd.DataFrame({
        "Brand": ["Joola", "Selkirk"],
        "Model": ["Perseus 16mm", "Luxx Control Air"],
        "Swing Weight": [117, 114],
        "Twist Weight": [6.1, 5.8],
        "Spin RPM": [2048, 1950],
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


class TestReadFromEnvBase64:
    def test_returns_none_when_env_not_set(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JOHNKEW_XLSX_B64", None)
            result = read_from_env_base64()
        assert result is None

    def test_returns_bytes_when_env_set(self):
        xlsx_bytes = _make_xlsx_bytes()
        encoded = base64.b64encode(xlsx_bytes).decode()
        with patch.dict(os.environ, {"JOHNKEW_XLSX_B64": encoded}):
            result = read_from_env_base64()
        assert result is not None
        assert len(result) > 0

    def test_returns_none_on_invalid_base64(self):
        with patch.dict(os.environ, {"JOHNKEW_XLSX_B64": "not-valid-base64!!!"}):
            result = read_from_env_base64()
        assert result is None


class TestDownloadFile:
    def test_returns_none_on_request_error(self):
        import requests
        with patch("scripts.fetch_johnkew.requests.get", side_effect=requests.RequestException):
            result = download_file("https://example.com/paddles.xlsx")
        assert result is None

    def test_returns_none_when_response_is_html(self):
        mock_resp = MagicMock()
        mock_resp.content = b"<html><body>Login required</body></html>"
        mock_resp.headers = {"content-type": "text/html"}
        mock_resp.raise_for_status = MagicMock()
        with patch("scripts.fetch_johnkew.requests.get", return_value=mock_resp):
            result = download_file("https://example.com/paddles.xlsx")
        assert result is None

    def test_returns_bytes_for_binary_response(self):
        xlsx_bytes = _make_xlsx_bytes()
        mock_resp = MagicMock()
        mock_resp.content = xlsx_bytes
        mock_resp.headers = {"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        mock_resp.raise_for_status = MagicMock()
        with patch("scripts.fetch_johnkew.requests.get", return_value=mock_resp):
            result = download_file("https://example.com/paddles.xlsx")
        assert result is not None
        assert len(result) > 0


class TestConvertToCsv:
    def test_converts_xlsx_to_csv_successfully(self, tmp_path):
        xlsx_bytes = _make_xlsx_bytes()
        output = str(tmp_path / "johnkew.csv")
        result = convert_to_csv(xlsx_bytes, output)
        assert result is True
        df = pd.read_csv(output)
        assert "Brand" in df.columns
        assert "Model" in df.columns
        assert len(df) == 2

    def test_returns_false_on_garbage_input(self, tmp_path):
        output = str(tmp_path / "johnkew.csv")
        result = convert_to_csv(b"not an excel file", output)
        assert result is False


class TestFetchJohnkewMain:
    def test_uses_base64_env_if_set(self, tmp_path):
        xlsx_bytes = _make_xlsx_bytes()
        encoded = base64.b64encode(xlsx_bytes).decode()
        out = str(tmp_path / "johnkew.csv")
        with patch.dict(os.environ, {"JOHNKEW_XLSX_B64": encoded}):
            result = fetch_johnkew_main(output=out)
        assert result is True
        assert Path(out).exists()

    def test_returns_false_when_no_content(self, tmp_path):
        out = str(tmp_path / "johnkew.csv")
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JOHNKEW_XLSX_B64", None)
        with patch("scripts.fetch_johnkew.read_from_env_base64", return_value=None), \
             patch("scripts.fetch_johnkew.download_with_playwright", return_value=False), \
             patch("scripts.fetch_johnkew.download_file", return_value=None), \
             patch("scripts.fetch_johnkew.scrape_page_for_share_link", return_value=None):
            result = fetch_johnkew_main(output=out)
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# fetch_pb_studio.py
# ═══════════════════════════════════════════════════════════════════════════════


class TestBlocksToDataframe:
    def _make_block(self, brand: str, model: str, core_mm: float | None = None) -> dict:
        props = {
            "o{Nq": [[brand]],
            "{S<Z": [[model]],
        }
        if core_mm is not None:
            props["fSUz"] = [[str(core_mm)]]
        return {"value": {"type": "page", "properties": props}}

    def test_parses_notion_blocks_to_rows(self):
        blocks = [
            self._make_block("Joola", "Perseus 16mm", 16.0),
            self._make_block("Selkirk", "Luxx Control Air"),
        ]
        df = blocks_to_dataframe(blocks)
        assert len(df) == 2
        assert "Brand" in df.columns
        assert "Model" in df.columns
        assert df.iloc[0]["Brand"] == "Joola"

    def test_skips_non_page_blocks(self):
        blocks = [
            {"value": {"type": "collection_view_page", "properties": {}}},
            self._make_block("Joola", "Perseus"),
        ]
        df = blocks_to_dataframe(blocks)
        assert len(df) == 1

    def test_skips_blocks_without_brand_or_model(self):
        blocks = [
            {"value": {"type": "page", "properties": {"fSUz": [["16.0"]]}}},  # no brand/model
        ]
        df = blocks_to_dataframe(blocks)
        assert len(df) == 0


class TestFetchPBStudioMain:
    def test_returns_false_when_no_rows(self, tmp_path):
        out = str(tmp_path / "pbstudio.csv")
        with patch("scripts.fetch_pb_studio.fetch_block_ids", return_value=[]), \
             patch("scripts.fetch_pb_studio.fetch_blocks", return_value=[]), \
             patch("scripts.fetch_pb_studio.blocks_to_dataframe", return_value=pd.DataFrame()):
            result = fetch_pbstudio_main(output=out)
        assert result is False

    def test_returns_true_when_rows_fetched(self, tmp_path):
        out = str(tmp_path / "pbstudio.csv")

        def _make_b(brand, model):
            return {"value": {"type": "page", "properties": {
                "o{Nq": [[brand]], "{S<Z": [[model]]
            }}}

        blocks = [_make_b("Joola", "Perseus"), _make_b("Selkirk", "Luxx")]
        with patch("scripts.fetch_pb_studio.fetch_block_ids", return_value=["id1", "id2"]), \
             patch("scripts.fetch_pb_studio.fetch_blocks", return_value=blocks):
            result = fetch_pbstudio_main(output=out)

        assert result is True
        df = pd.read_csv(out)
        assert "Brand" in df.columns
        assert len(df) == 2
