"""
Scrape JustPaddles (Paddle Lab)
Extracts Real Weight, Swing Weight, and Twist Weight from JustPaddles product pages
using Playwright to navigate the site.

Usage (spec enrichment):
  docker compose exec backend_v3 python scripts/scrape_justpaddles.py
  docker compose exec backend_v3 python scripts/scrape_justpaddles.py --dry-run

Usage (market-offer ingestion):
  docker compose exec backend_v3 python scripts/scrape_justpaddles.py --ingest
"""

import sys
import asyncio
import argparse
from pathlib import Path

from playwright.async_api import async_playwright
from sqlmodel import Session, select
from sqlalchemy.orm import attributes

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import sync_engine, init_db_sync
from app.db.ingestor import ingest_rows
from app.models import Brand, PaddleMaster
from app.models.paddle import calculate_specs_confidence
from app.models.store import Store

SOURCE_NAME = "justpaddles"
STORE_NAME = "Just Paddles"
DOMAIN = "www.justpaddles.com.br"

KNOWN_BRANDS = [
    "Selkirk",
    "Joola",
    "Onix",
    "Engage",
    "Franklin",
    "Paddletek",
    "ProXR",
    "Gamma",
    "Head",
    "Babolat",
    "ProSpin",
    "Dbear",
    "Kleren",
    "Voltrics",
    "Rally",
    "Rocket",
    "Nexus",
    "Neon",
]


def _parse_price(text: str) -> float:
    import re

    text = text.replace("R$", "").replace("$", "").strip()
    text = re.sub(r"(\d)\.(\d{3})", r"\1", text)
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _parse_title(title: str):
    title = title.strip()
    title_lower = title.lower()
    for brand in KNOWN_BRANDS:
        if title_lower.startswith(brand.lower()):
            model = title[len(brand) :].strip("- /").strip()
            return brand, model
    parts = title.split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    return None, title


async def fetch_justpaddles_products() -> list[dict]:
    from playwright.async_api import async_playwright

    products = []
    category_urls = [
        f"https://{DOMAIN}/collections/pickleball",
        f"https://{DOMAIN}/collections/raquetes",
        f"https://{DOMAIN}/products",
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in category_urls:
            try:
                resp = await page.goto(url, timeout=20000)
                if not resp or resp.status >= 400:
                    continue
                await page.wait_for_load_state("networkidle", timeout=15000)
                await page.wait_for_timeout(3000)

                items = await page.query_selector_all(
                    "[data-product-id], .product-item, .product-card, "
                    "li.product, .js-item-product, article[data-handle]"
                )
                if not items:
                    items = await page.query_selector_all("a[href*='/products/']")

                print(f"  [{url}] Found {len(items)} items")
                seen = set()

                for item in items:
                    href = (
                        await item.get_attribute("href") if hasattr(item, "get_attribute") else ""
                    )
                    if not href:
                        try:
                            link_el = await item.query_selector("a[href*='/products/']")
                            if link_el:
                                href = await link_el.get_attribute("href")
                        except Exception:
                            pass

                    if not href or "/products/" not in str(href):
                        continue
                    product_url = (
                        href if str(href).startswith("http") else f"https://{DOMAIN}{href}"
                    )
                    if product_url in seen:
                        continue
                    seen.add(product_url)

                    try:
                        title_el = await item.query_selector(
                            "h2, h3, .title, .product-title, .name"
                        )
                        price_el = await item.query_selector(".price, .product-price, .amount")
                        title = await title_el.inner_text() if title_el else ""
                        price_text = await price_el.inner_text() if price_el else "0"
                    except Exception:
                        continue

                    if not title:
                        continue

                    brand, model = _parse_title(title)
                    if not brand or not model:
                        continue

                    price = _parse_price(price_text)
                    if price <= 0:
                        price = 999.0

                    products.append(
                        {
                            "brand_name": brand,
                            "model_name": model,
                            "price_brl": str(price),
                            "product_url": product_url,
                            "image_url": "",
                        }
                    )
                    print(f"    {brand} — {model} — R$ {price:.2f}")

            except Exception as e:
                print(f"  ⚠️  {url}: {e}")
                continue

        await browser.close()

    print(f"\n  Total products collected: {len(products)}")
    return products


async def run_market_offer_ingestion():
    print(f"🏓 Scraping {STORE_NAME} for market offers...")
    rows = await fetch_justpaddles_products()

    init_db_sync()
    with Session(sync_engine) as session:
        store = session.exec(select(Store).where(Store.name == STORE_NAME)).one()
        stats = ingest_rows(rows, store_id=store.id, session=session)
        session.commit()
    print(f"\n{'=' * 60}")
    print("✅ JUST PADDLES INGESTION COMPLETE")
    print(f"   Created:  {stats['created']}")
    print(f"   Updated: {stats['updated']}")
    print(f"   Skipped: {stats['skipped']}")


async def scrape_paddle_lab(page, search_query: str):
    """Searches for a paddle and attempts to extract its Paddle Lab stats."""
    # 1. Search for the paddle
    search_url = f"https://www.justpaddles.com/products/?s={search_query.replace(' ', '+')}"
    await page.goto(search_url)

    # Check if we were redirected to a product page directly
    if "/product/" in page.url or "/products/paddle/" in page.url:
        return await extract_lab_data(page)

    # Otherwise, try to click the first search result
    try:
        # Wait for product grid
        await page.wait_for_selector(".product-grid-item", timeout=5000)
        first_product = await page.query_selector(".product-grid-item a")
        if first_product:
            await first_product.click()
            await page.wait_for_load_state("networkidle")
            return await extract_lab_data(page)
    except Exception:
        print(f"  [Search] No results or timeout for {search_query!r}")
        return None

    return None


async def extract_lab_data(page) -> dict:
    """Extracts Paddle Lab stats from a loaded product page."""
    data = {}

    try:
        # JustPaddles often puts the Babolat machine lab data in a specific section
        # Look for the Paddle Lab section
        lab_section = await page.query_selector("text='Paddle Lab'")
        if not lab_section:
            return data

        # Extraction logic depends on actual DOM, this is a placeholder structure
        # typically they have definition lists or tables
        # Example: <dt>Swing Weight</dt><dd>116</dd>

        sw_elem = await page.query_selector(
            "xpath=//dt[contains(text(), 'Swing Weight')]/following-sibling::dd[1]"
        )
        if sw_elem:
            txt = await sw_elem.inner_text()
            if txt.isdigit():
                data["swing_weight"] = int(txt)

        tw_elem = await page.query_selector(
            "xpath=//dt[contains(text(), 'Twist Weight')]/following-sibling::dd[1]"
        )
        if tw_elem:
            txt = await tw_elem.inner_text()
            try:
                data["twist_weight"] = float(txt)
            except ValueError:
                pass

    except Exception as e:
        print(f"  [Extract] Error extracting data on {page.url}: {e}")

    return data


async def run_scraper(dry_run: bool = False, limit: int = None):
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"🧠 JustPaddles Scraper Pipeline — PostgreSQL [{mode}]")
    print("=" * 60)

    init_db_sync()

    with Session(sync_engine) as session:
        # Filter for paddles that actually need verification
        paddles = session.exec(
            select(PaddleMaster)
            .join(Brand, PaddleMaster.brand_id == Brand.id)
            .where(PaddleMaster.specs_confidence < 1.0)
        ).all()

        brands = {b.id: b for b in session.exec(select(Brand)).all()}

        if limit:
            paddles = paddles[:limit]

        print(f"🎾 DB: {len(paddles)} paddles to check\n")

        updated_count = 0
        no_match = 0

        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent pages to avoid blocking

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            async def process_paddle(paddle):
                nonlocal updated_count, no_match
                async with semaphore:
                    brand = brands.get(paddle.brand_id)
                    if not brand:
                        return

                    query = f"{brand.name} {paddle.model_name}"
                    print(f"🔍 Searching: {query!r}...")

                    # Create a fresh page for each request to avoid state issues
                    p_page = await browser.new_page()
                    try:
                        lab_data = await scrape_paddle_lab(p_page, query)

                        if not lab_data:
                            no_match += 1
                            return

                        print(f"  ✅ Found Lab Data: {lab_data}")

                        updates = {}
                        if "swing_weight" in lab_data and not paddle.swing_weight:
                            updates["swing_weight"] = lab_data["swing_weight"]
                        if "twist_weight" in lab_data and not paddle.twist_weight:
                            updates["twist_weight"] = lab_data["twist_weight"]

                        # Update validation sources
                        current_sources = list(paddle.validation_sources or [])
                        if SOURCE_NAME not in current_sources:
                            updates["validation_sources"] = current_sources + [SOURCE_NAME]

                        if updates:
                            updated_count += 1
                            if not dry_run:
                                for field, value in updates.items():
                                    setattr(paddle, field, value)

                                attributes.flag_modified(paddle, "validation_sources")
                                paddle.specs_confidence = calculate_specs_confidence(paddle)
                                session.add(paddle)  # Ensure it's tracked
                                session.commit()
                    finally:
                        await p_page.close()

            # Process in batches or gather all if small
            await asyncio.gather(*(process_paddle(p) for p in paddles))
            await browser.close()

        print(f"\n{'=' * 60}")
        print(f"✅ JUSTPADDLES SCRAPING {'PREVIEW' if dry_run else 'COMPLETE'}")
        print(f"   🟢 Updated Paddles: {updated_count}")
        print(f"   🔴 No match/data:   {no_match}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to DB")
    parser.add_argument("--limit", type=int, help="Limit number of paddles to process")
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Run market-offer ingestion instead of spec enrichment",
    )
    args = parser.parse_args()

    if args.ingest:
        asyncio.run(run_market_offer_ingestion())
    else:
        asyncio.run(run_scraper(dry_run=args.dry_run, limit=args.limit))


if __name__ == "__main__":
    main()
