"""
Fetch JohnKew Paddle Database and convert to CSV.

Downloads the publicly shared Excel database from JohnKew's OneDrive.
Uses two strategies:
  1. JOHNKEW_XLSX_B64 env var (fastest, no network — recommended for CI)
  2. Playwright headless browser (downloads the public xlsx automatically)

No auth required — the database is publicly shared.

Usage:
  python scripts/fetch_johnkew.py           # saves to /tmp/johnkew.csv
  python scripts/fetch_johnkew.py --out /tmp/custom.csv

Setup for CI (one-time):
  # Download the xlsx from https://1drv.ms/x/c/fce22c692072ad45/IQRixkqR7I5zS7KxnA0UNcFLAUfmJ_cg8HFvyQC34mmvQE8
  base64 -w 0 Paddle-Metrics-Master.xlsx
  # Add the output as JOHNKEW_XLSX_B64 in GitHub Secrets
"""
import sys
import io
import os
import json
import base64
import argparse
import tempfile
from pathlib import Path

import requests
import pandas as pd


ONEDRIVE_SHARE_URL = "https://1drv.ms/x/c/fce22c692072ad45/IQRixkqR7I5zS7KxnA0UNcFLAUfmJ_cg8HFvyQC34mmvQE8"
DEFAULT_OUTPUT = "/tmp/johnkew.csv"


def read_from_env_base64() -> bytes | None:
    """
    Read the XLSX file from the JOHNKEW_XLSX_B64 environment variable.
    This is the recommended CI approach: encode the file once, store as GitHub Secret.

    To generate:
      base64 -w 0 Paddle-Metrics-Master.xlsx
      # Add output as JOHNKEW_XLSX_B64 in GitHub Secrets
    """
    encoded = os.environ.get("JOHNKEW_XLSX_B64", "").strip()
    if not encoded:
        return None
    try:
        content = base64.b64decode(encoded)
        print(f"✅ Read {len(content):,} bytes from JOHNKEW_XLSX_B64 env var")
        return content
    except Exception as e:
        print(f"⚠️  Failed to decode JOHNKEW_XLSX_B64: {e}")
        return None


def download_with_playwright(share_url: str, output_xlsx: str) -> bool:
    """
    Use Playwright to get the authenticated download URL for the publicly shared file.
    When OneDrive loads in the browser, it calls the Graph API which returns a
    @content.downloadUrl with a short-lived tempauth token. We intercept that
    response and use it to download the actual xlsx file.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("⚠️  Playwright not available")
        return False

    print(f"🌐 Using Playwright to resolve download URL: {share_url}")

    download_url: str | None = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        def handle_response(response):
            nonlocal download_url
            if "microsoftpersonalcontent.com/_api/v2.0/shares" in response.url and not download_url:
                try:
                    data = json.loads(response.text())
                    dl = data.get("@content.downloadUrl", "")
                    if dl:
                        download_url = dl
                        print("📥 Found download URL via Graph API intercept")
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            page.goto(share_url, wait_until="domcontentloaded", timeout=30000)
            # Wait for the Graph API request to complete
            page.wait_for_timeout(8000)
        except Exception as e:
            print(f"⚠️  Playwright navigation: {e}")
        finally:
            browser.close()

    if not download_url:
        print("⚠️  Playwright: Graph API call not intercepted")
        return False

    # Download the xlsx using the tempauth URL
    print("⬇️  Downloading xlsx via tempauth URL...")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(download_url, headers=headers, timeout=60, allow_redirects=True)
        r.raise_for_status()
        content = r.content
        if b"<html" in content[:200].lower():
            print("⚠️  Downloaded content appears to be HTML — token may have expired")
            return False
        print(f"✅ Downloaded {len(content):,} bytes")
        Path(output_xlsx).parent.mkdir(parents=True, exist_ok=True)
        Path(output_xlsx).write_bytes(content)
        return True
    except Exception as e:
        print(f"❌ Download via tempauth URL failed: {e}")
        return False




def download_file(url: str) -> bytes | None:
    """Download raw bytes from URL, returns None if response is HTML."""
    import requests
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=60, stream=True, allow_redirects=True)
        r.raise_for_status()
        content = r.content
        ct = r.headers.get("content-type", "")
        print(f"📦 Downloaded {len(content):,} bytes (Content-Type: {ct})")
        if b"<html" in content[:200].lower():
            print("⚠️  Response appears to be HTML, not a binary file")
            return None
        return content
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None


def scrape_page_for_share_link() -> str | None:
    """Scrape the JohnKew page to find any updated share link."""
    import requests
    from bs4 import BeautifulSoup
    import re
    print(f"🔍 Scraping JohnKew page...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get("https://www.johnkewpickleball.com/paddle-database", headers=headers, timeout=30)
        r.raise_for_status()
        matches = re.findall(r"https?://1drv\.ms/x/[^\s\"'<>&]+", r.text)
        if matches:
            print(f"✅ Found share link: {matches[0][:80]}")
            return matches[0]
    except Exception:
        pass
    return None


def convert_to_csv(content: bytes, output_path: str) -> bool:
    """Convert Excel bytes to CSV."""
    for engine in ("openpyxl", "xlrd"):
        try:
            df = pd.read_excel(io.BytesIO(content), engine=engine)
            print(f"📊 Parsed {len(df)} rows × {len(df.columns)} columns (engine={engine})")
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            print(f"✅ Saved CSV to: {output_path}")
            return True
        except Exception as e:
            print(f"⚠️  Engine '{engine}' failed: {e}")
    print("❌ Failed to parse Excel content")
    return False


def main(output: str = DEFAULT_OUTPUT) -> bool:
    print(f"🎯 JohnKew Fetch Pipeline → {output}")
    print("=" * 60)

    # Strategy 0: Read from JOHNKEW_XLSX_B64 env/secret (fastest, no network)
    content = read_from_env_base64()
    if content:
        return convert_to_csv(content, output)

    # Strategy 1: Playwright browser download (works for publicly shared files)
    with tempfile.TemporaryDirectory() as tmpdir:
        xlsx_path = str(Path(tmpdir) / "johnkew.xlsx")
        share_url = scrape_page_for_share_link() or ONEDRIVE_SHARE_URL

        if download_with_playwright(share_url, xlsx_path):
            if Path(xlsx_path).exists():
                content = Path(xlsx_path).read_bytes()
                return convert_to_csv(content, output)

    # Strategy 2: Plain HTTP fallback (may work if the URL structure changes)
    print("⚠️  Playwright failed, trying plain HTTP...")
    content = download_file(ONEDRIVE_SHARE_URL)
    if content:
        return convert_to_csv(content, output)

    print("❌ Could not download JohnKew database.")
    print("💡 Set JOHNKEW_XLSX_B64 GitHub Secret to bypass network:")
    print("   base64 -w 0 Paddle-Metrics-Master.xlsx")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch JohnKew paddle database")
    parser.add_argument("--out", default=DEFAULT_OUTPUT, help="Output CSV path")
    args = parser.parse_args()

    success = main(output=args.out)
    sys.exit(0 if success else 1)
