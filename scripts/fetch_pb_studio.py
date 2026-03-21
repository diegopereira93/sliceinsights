"""
Fetch Pickleball Studio Notion database and export to CSV.

Reads the public Notion database at thepickleballstudio.notion.site and
exports paddle data to /tmp/pbstudio.csv.
No auth token required — the database is publicly accessible.

Usage:
  python scripts/fetch_pb_studio.py           # saves to /tmp/pbstudio.csv
  python scripts/fetch_pb_studio.py --out /tmp/custom.csv
  python scripts/fetch_pb_studio.py --token {NOTION_TOKEN}  # official API
"""
import sys
import argparse
from pathlib import Path
from typing import Any

import requests
import pandas as pd

# Public Notion database — thepickleballstudio.notion.site/5bdf3ee7...
NOTION_PAGE_ID = "5bdf3ee7-52c9-40eb-a864-a81bc3281164"
NOTION_COLLECTION_ID = "3c5f9880-81b2-4ace-b83c-46374c8281c0"
NOTION_SPACE_ID = "506f2e06-5b8c-449b-8da1-caa63bc40912"
NOTION_VIEW_ID = "a5170d43-e5ab-4573-b18f-48c363cce7ec"

NOTION_API_VERSION = "2022-06-28"
DEFAULT_OUTPUT = "/tmp/pbstudio.csv"
TIMEOUT = 60
PAGE_LIMIT = 9999

# Schema: opaque Notion property keys → human-readable column names
SCHEMA_MAP = {
    "o{Nq": "Brand",
    "{S<Z": "Model",
    "fSUz": "Core Thickness (mm)",
    "Lfds": "Swing Weight",
    "KmOn": "Twist Weight",
    "PD||": "Balance",
    "D>v]": "Grams",
    "C{vB": "ID",
    "Sk;V": "Face Material",
    "lvSm": "Core Material",
    "RLTk": "Shape",
    "`R^P": "Price",
    "o>uL": "Spin RPM",
    "bEnc": "Grip Length",
    "kKLs": "Grip Thickness",
    "lVld": "Purchase Link",
    "lZ`G": "Discount",
    "tI]y": "Discount Code",
    "_b^^": "YouTube Review",
    "{@PA": "Advertised Weight",
    "TOIH": "Date",
    "ASxE": "Score",
    "title": "_title",  # usually not useful (row title)
}

_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def _rich_text_to_str(value: Any) -> Any:
    """Convert a Notion rich-text array [[text, ...], ...] to a plain string."""
    if not isinstance(value, list):
        return value
    parts = []
    for item in value:
        if isinstance(item, list) and item:
            text = item[0]
            if isinstance(text, str) and text not in (",", ""):
                parts.append(text)
        elif isinstance(item, str) and item not in (",", ""):
            parts.append(item)
    result = "".join(parts).strip()
    return result if result else None


def fetch_block_ids(limit: int = PAGE_LIMIT) -> list[str]:
    """Get all row block IDs from the PB Studio collection."""
    url = "https://www.notion.so/api/v3/queryCollection"
    body = {
        "collection": {"id": NOTION_COLLECTION_ID, "spaceId": NOTION_SPACE_ID},
        "collectionView": {"id": NOTION_VIEW_ID, "spaceId": NOTION_SPACE_ID},
        "loader": {
            "type": "reducer",
            "reducers": {
                "collection_group_results": {
                    "type": "results",
                    "limit": limit,
                }
            },
            "searchQuery": "",
            "userTimeZone": "America/Sao_Paulo",
        },
    }
    r = requests.post(url, headers=_HEADERS, json=body, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    block_ids = (
        data.get("result", {})
        .get("reducerResults", {})
        .get("collection_group_results", {})
        .get("blockIds", [])
    )
    print(f"📋 Found {len(block_ids)} rows in Notion database")
    return block_ids


def fetch_blocks(block_ids: list[str]) -> list[dict]:
    """Fetch block properties for a list of block IDs via syncRecordValues."""
    url = "https://www.notion.so/api/v3/syncRecordValues"
    # Batch in groups of 100 to avoid oversized requests
    all_blocks = []
    batch_size = 100

    for i in range(0, len(block_ids), batch_size):
        batch = block_ids[i: i + batch_size]
        body = {
            "requests": [
                {"pointer": {"table": "block", "id": bid, "spaceId": NOTION_SPACE_ID}, "version": -1}
                for bid in batch
            ]
        }
        r = requests.post(url, headers=_HEADERS, json=body, timeout=TIMEOUT)
        r.raise_for_status()
        blocks_map = r.json().get("recordMap", {}).get("block", {})
        all_blocks.extend(blocks_map.values())
        print(f"  ↳ Fetched batch {i // batch_size + 1}: {len(batch)} blocks")

    return all_blocks


def blocks_to_dataframe(blocks: list[dict]) -> pd.DataFrame:
    """Convert Notion block records to a clean DataFrame using the schema map."""
    records = []
    for item in blocks:
        value = item.get("value", {})
        if not isinstance(value, dict) or value.get("type") not in ("page",):
            continue
        props = value.get("properties", {})
        if not props:
            continue

        row = {}
        for raw_key, col_name in SCHEMA_MAP.items():
            if col_name.startswith("_"):
                continue
            raw_val = props.get(raw_key)
            row[col_name] = _rich_text_to_str(raw_val) if raw_val is not None else None

        # Only include rows that have at least Brand or Model
        if row.get("Brand") or row.get("Model"):
            records.append(row)

    return pd.DataFrame(records)


def fetch_notion_database_official(token: str) -> pd.DataFrame | None:
    """Fetch using the official Notion API (requires integration token)."""
    url = f"https://api.notion.com/v1/databases/{NOTION_COLLECTION_ID}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }
    rows, cursor = [], None
    while True:
        body: dict[str, Any] = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        r = requests.post(url, headers=headers, json=body, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        rows.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    print(f"📦 Fetched {len(rows)} rows via official Notion API")
    records = []
    for page in rows:
        props = page.get("properties", {})
        record: dict = {}
        for key, val in props.items():
            ptype = val.get("type", "")
            if ptype == "title":
                record[key] = " ".join(t.get("plain_text", "") for t in val.get("title", []))
            elif ptype == "rich_text":
                record[key] = " ".join(t.get("plain_text", "") for t in val.get("rich_text", []))
            elif ptype == "number":
                record[key] = val.get("number")
            elif ptype == "select":
                sel = val.get("select")
                record[key] = sel.get("name") if sel else None
            elif ptype == "multi_select":
                record[key] = ", ".join(s.get("name", "") for s in val.get("multi_select", []))
        records.append(record)
    return pd.DataFrame(records) if records else None


def main(output: str = DEFAULT_OUTPUT, token: str | None = None) -> bool:
    """Fetch PB Studio Notion database and save to CSV."""
    print(f"🎯 PB Studio Fetch Pipeline → {output}")
    print("=" * 60)

    df = None

    # Strategy 1: Official API with token (if available)
    if token:
        print("🔐 Using official Notion API with token...")
        try:
            df = fetch_notion_database_official(token)
            if df is not None and not df.empty:
                print(f"✅ Official API returned {len(df)} rows")
        except Exception as e:
            print(f"⚠️  Official API failed: {e}")
            df = None

    # Strategy 2: Unofficial public API (no auth required)
    if df is None or df.empty:
        print("🌐 Using unofficial Notion API (no auth required)...")
        try:
            block_ids = fetch_block_ids()
            if not block_ids:
                print("❌ No rows found via unofficial API")
                return False
            blocks = fetch_blocks(block_ids)
            df = blocks_to_dataframe(blocks)
        except requests.RequestException as e:
            print(f"❌ Notion API request failed: {e}")
            return False

    if df is None or df.empty:
        print("❌ Failed to fetch any rows from PB Studio Notion database")
        return False

    df = df.dropna(how="all")
    print(f"📊 {len(df)} rows × {len(df.columns)} columns")

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"✅ Saved CSV to: {output}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch PB Studio Notion database")
    parser.add_argument("--out", default=DEFAULT_OUTPUT, help="Output CSV path")
    parser.add_argument("--token", default=None, help="Notion API token (optional)")
    args = parser.parse_args()

    success = main(output=args.out, token=args.token)
    sys.exit(0 if success else 1)
