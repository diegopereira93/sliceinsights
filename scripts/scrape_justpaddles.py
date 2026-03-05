"""
Scrape JustPaddles (Paddle Lab)
Extracts Real Weight, Swing Weight, and Twist Weight from JustPaddles product pages
using Playwright to navigate the site.

Usage:
  docker compose exec backend_v3 python scripts/scrape_justpaddles.py
  docker compose exec backend_v3 python scripts/scrape_justpaddles.py --dry-run
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
from app.models import Brand, PaddleMaster
from app.models.paddle import calculate_specs_confidence

SOURCE_NAME = "justpaddles"

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
    except Exception as e:
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
        
        sw_elem = await page.query_selector("xpath=//dt[contains(text(), 'Swing Weight')]/following-sibling::dd[1]")
        if sw_elem:
             txt = await sw_elem.inner_text()
             if txt.isdigit():
                 data['swing_weight'] = int(txt)
                 
        tw_elem = await page.query_selector("xpath=//dt[contains(text(), 'Twist Weight')]/following-sibling::dd[1]")
        if tw_elem:
             txt = await tw_elem.inner_text()
             try:
                 data['twist_weight'] = float(txt)
             except ValueError:
                 pass
                 
    except Exception as e:
        print(f"  [Extract] Error extracting data on {page.url}: {e}")
        
    return data

async def run_scraper(dry_run: bool = False):
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"🧠 JustPaddles Scraper Pipeline — PostgreSQL [{mode}]")
    print("=" * 60)

    init_db_sync()

    with Session(sync_engine) as session:
        paddles = session.exec(
            select(PaddleMaster).join(Brand, PaddleMaster.brand_id == Brand.id)
        ).all()
        brands = {b.id: b for b in session.exec(select(Brand)).all()}

        print(f"🎾 DB: {len(paddles)} paddles to check\n")
        
        updated_count = 0
        no_match = 0
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Identify paddles missing specs
            for paddle in paddles:
                # Skip if already fully confident
                if paddle.specs_confidence == 1.0:
                    continue
                    
                brand = brands.get(paddle.brand_id)
                if not brand:
                    continue
                    
                query = f"{brand.name} {paddle.model_name}"
                print(f"🔍 Searching: {query!r}...")
                
                lab_data = await scrape_paddle_lab(page, query)
                
                if not lab_data:
                    no_match += 1
                    continue
                    
                print(f"  ✅ Found Lab Data: {lab_data}")
                
                updates = {}
                if 'swing_weight' in lab_data and not paddle.swing_weight:
                    updates['swing_weight'] = lab_data['swing_weight']
                if 'twist_weight' in lab_data and not paddle.twist_weight:
                    updates['twist_weight'] = lab_data['twist_weight']
                    
                # Update validation sources
                current_sources = list(paddle.validation_sources or [])
                if SOURCE_NAME not in current_sources:
                    updates['validation_sources'] = current_sources + [SOURCE_NAME]
                    
                if updates:
                    updated_count += 1
                    if not dry_run:
                        for field, value in updates.items():
                            setattr(paddle, field, value)
                            
                        attributes.flag_modified(paddle, "validation_sources")
                        paddle.specs_confidence = calculate_specs_confidence(paddle)
                        session.commit()
                        
            await browser.close()
            
        print(f"\n{'=' * 60}")
        print(f"✅ JUSTPADDLES SCRAPING {'PREVIEW' if dry_run else 'COMPLETE'}")
        print(f"   🟢 Updated Paddles: {updated_count}")
        print(f"   🔴 No match/data:   {no_match}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to DB")
    args = parser.parse_args()
    asyncio.run(run_scraper(dry_run=args.dry_run))

if __name__ == "__main__":
    main()
