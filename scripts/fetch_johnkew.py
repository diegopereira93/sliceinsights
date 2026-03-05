"""
Fetch JohnKew Paddle Database and convert to CSV.

Automatically downloads the public Excel database from JohnKew's OneDrive share,
converts it to CSV, and saves it to /tmp/johnkew.csv.
No secrets required — the database is publicly shared.

Usage:
  python scripts/fetch_johnkew.py           # saves to /tmp/johnkew.csv
  python scripts/fetch_johnkew.py --out /tmp/custom.csv
"""
import sys
import re
import io
import argparse
from pathlib import Path

import requests
import pandas as pd

# Stable OneDrive share link — publicly shared by JohnKew on their paddle-database page
ONEDRIVE_SHARE_LINK = "https://1drv.ms/x/c/fce22c692072ad45/IQRixkqR7I5zS7KxnA0UNcFLAUfmJ_cg8HFvyQC34mmvQE8"
# Stable file identifiers extracted from the share link redirect (rarely change)
ONEDRIVE_CID = "fce22c692072ad45"
ONEDRIVE_RESID = "FCE22C692072AD45!s914ac6628eec4b73b2b19c0d1435c14b"  # from redirect URL
ONEDRIVE_UNIQUE_ID = "914ac662-8eec-4b73-b2b1-9c0d1435c14b"  # UUID inside resid

# Fallback: scrape the JohnKew page to find any updated share link
JOHNKEW_PAGE_URL = "https://www.johnkewpickleball.com/paddle-database"
DEFAULT_OUTPUT = "/tmp/johnkew.csv"
TIMEOUT = 60  # seconds


def get_onedrive_download_url(cid: str, resid: str) -> str:
    """
    Build the OneDrive direct download URL using cid and resid.
    This approach works for publicly shared files.
    """
    # OneDrive direct download format
    return f"https://api.onedrive.com/v1.0/shares/u!{_encode_share_url(ONEDRIVE_SHARE_LINK)}/root/content"


def _encode_share_url(url: str) -> str:
    """Encode a share URL to base64url for use in OneDrive API."""
    import base64
    b64 = base64.urlsafe_b64encode(url.encode()).rstrip(b"=")
    return b64.decode()


def resolve_onedrive_download_url() -> str | None:
    """
    Resolve the 1drv.ms share link to a real binary download URL.
    Uses the OneDrive sharing API to get a direct content URL.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SliceInsightsBot/1.0)"}

    # Strategy 1: Microsoft personal content direct download via unique ID
    direct_url = (
        f"https://my.microsoftpersonalcontent.com/personal/{ONEDRIVE_CID}"
        f"/_layouts/15/download.aspx?UniqueId={ONEDRIVE_UNIQUE_ID}"
    )
    print(f"🔗 Trying direct download: {direct_url[:100]}")
    try:
        r = requests.head(direct_url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code in (200, 302):
            return direct_url
    except requests.RequestException:
        pass

    # Strategy 2: OneDrive API sharing endpoint (works for public shares)
    encoded = _encode_share_url(ONEDRIVE_SHARE_LINK)
    api_url = f"https://api.onedrive.com/v1.0/shares/u!{encoded}/root/content"
    print(f"🔗 Trying OneDrive API: {api_url[:100]}")
    try:
        r = requests.head(api_url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code in (200, 302):
            return api_url
    except requests.RequestException:
        pass

    # Strategy 3: Use resid to build the download URL
    resid_url = (
        f"https://onedrive.live.com/download.aspx"
        f"?cid={ONEDRIVE_CID}&resid={ONEDRIVE_RESID}&authkey="
    )
    print(f"🔗 Trying resid download: {resid_url[:100]}")

    return resid_url


def scrape_page_for_share_link() -> str | None:
    """Scrape the JohnKew page to find the current OneDrive/Excel share link."""
    print(f"🔍 Scraping JohnKew page for share link: {JOHNKEW_PAGE_URL}")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SliceInsightsBot/1.0)"}
    try:
        r = requests.get(JOHNKEW_PAGE_URL, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"⚠️  Page fetch failed: {e}")
        return None

    matches = re.findall(r"https?://1drv\.ms/x/[^\s\"'<>&]+", r.text)
    if matches:
        print(f"✅ Found share link on page: {matches[0][:80]}...")
        return matches[0]
    return None


def download_file(url: str) -> bytes | None:
    """Download raw bytes from URL."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SliceInsightsBot/1.0)"}
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT, stream=True, allow_redirects=True)
        r.raise_for_status()
        content = r.content
        ct = r.headers.get("content-type", "")
        print(f"📦 Downloaded {len(content):,} bytes (Content-Type: {ct})")
        # Check if it's actually an Excel file (not HTML)
        if b"<html" in content[:200].lower():
            print("⚠️  Response appears to be HTML, not a binary file")
            return None
        return content
    except requests.RequestException as e:
        print(f"❌ Download failed: {e}")
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
    print("❌ Failed to parse Excel content with any engine")
    return False


def read_from_env_base64() -> bytes | None:
    """
    Read the XLSX file from the JOHNKEW_XLSX_B64 environment variable.
    This is the recommended CI approach: encode the file once and store as a GitHub Secret.

    To generate the base64 string locally:
      base64 -w 0 Paddle-Metrics-Master.xlsx
    Then add the output as JOHNKEW_XLSX_B64 in GitHub Secrets.
    """
    import os
    import base64
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


def main(output: str = DEFAULT_OUTPUT) -> bool:
    print(f"🎯 JohnKew Fetch Pipeline → {output}")
    print("=" * 60)

    # Strategy 0: Read from JOHNKEW_XLSX_B64 GitHub Secret (recommended for CI)
    content = read_from_env_base64()
    if content:
        return convert_to_csv(content, output)

    # Strategy 1: Known stable direct download via personalized content URL
    dl_url = resolve_onedrive_download_url()
    content = download_file(dl_url)

    # Strategy 2: Scrape the page for an updated share link and try API
    if not content:
        print("⚠️  Direct download failed, scraping page for updated link...")
        page_link = scrape_page_for_share_link()
        if page_link:
            encoded = _encode_share_url(page_link)
            api_url = f"https://api.onedrive.com/v1.0/shares/u!{encoded}/root/content"
            content = download_file(api_url)

    if not content:
        print("❌ Could not download JohnKew database. The file may require browser authentication.")
        print("💡 Tip: Download manually from https://1drv.ms/x/c/fce22c692072ad45/IQRixkqR7I5zS7KxnA0UNcFLAUfmJ_cg8HFvyQC34mmvQE8")
        print("       then add it as GitHub Secret: JOHNKEW_XLSX_BASE64 (base64-encoded file content)")
        return False

    return convert_to_csv(content, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch JohnKew paddle database")
    parser.add_argument("--out", default=DEFAULT_OUTPUT, help="Output CSV path")
    args = parser.parse_args()

    success = main(output=args.out)
    sys.exit(0 if success else 1)
