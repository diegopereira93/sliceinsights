"""
Detailed Product Page Scraper — Extracts technical specs from Brazilian store product pages.

Targets:
  - joola.com.br: Structured specs in .metafield-row (click "Especificação" tab)
  - brazilpickleballstore.com.br: Unstructured text in .user-content (regex parsing)

Run:
  python scripts/scrape_product_specs.py --store joola
  python scripts/scrape_product_specs.py --dry-run --store joola  # preview URLs only
"""
import asyncio
import re
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

STORE_SLUG_TO_ID = {
    "joola": 2,
    "brazil_pickleball_store": 1,
}


# ─── PT-BR → EN Mappings ─────────────────────────────────────────────────────

FACE_MATERIAL_MAP = {
    "carbono": "CARBON",
    "carbon": "CARBON",
    "fibra de carbono": "CARBON",
    "raw carbon fiber": "CARBON",
    "charged carbon": "CARBON",
    "graphite": "CARBON",
    "grafite": "CARBON",
    "fibra de vidro": "FIBERGLASS",
    "fiberglass": "FIBERGLASS",
    "composite": "FIBERGLASS",
    "kevlar": "KEVLAR",
    "hybrid": "HYBRID",
    "híbrido": "HYBRID",
    "híbrida": "HYBRID",
}

SHAPE_MAP = {
    "elongated": "ELONGATED",
    "elongada": "ELONGATED",
    "blade": "ELONGATED",
    "wide body": "WIDEBODY",
    "widebody": "WIDEBODY",
    "wide": "WIDEBODY",
    "standard": "STANDARD",
    "clássico": "STANDARD",
    "classic": "STANDARD",
}

CORE_MATERIAL_MAP = {
    "polímero": "Polymer Honeycomb",
    "polymer": "Polymer Honeycomb",
    "polymer honeycomb": "Polymer Honeycomb",
    "polímero colmeia": "Polymer Honeycomb",
    "polipropileno": "Polymer Honeycomb",
    "propulsion core": "Polymer Honeycomb",
    "nomex": "Nomex Honeycomb",
    "aluminum": "Aluminum Honeycomb",
    "alumínio": "Aluminum Honeycomb",
}


def map_face_material(text: str) -> str | None:
    t = text.lower().strip()
    for key, val in FACE_MATERIAL_MAP.items():
        if key in t:
            return val
    return None


def map_shape(text: str) -> str | None:
    t = text.lower().strip()
    for key, val in SHAPE_MAP.items():
        if key in t:
            return val
    return None


def map_core_material(text: str) -> str | None:
    t = text.lower().strip()
    for key, val in CORE_MATERIAL_MAP.items():
        if key in t:
            return val
    return None


def extract_mm(text: str) -> float | None:
    """Extract millimeter measurement from text."""
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*mm', text, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(',', '.'))
    return None


def extract_weight_g(text: str) -> float | None:
    """Extract weight in grams from text like '226.8g' or '226,8 g'."""
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*g(?:ramas?)?', text, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(',', '.'))
    return None


def extract_cm(text: str) -> float | None:
    """Extract centimeter measurement."""
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*cm', text, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(',', '.'))
    return None


# ─── Joola.com.br Scraper ────────────────────────────────────────────────────

async def scrape_joola_page(page, url: str, paddle_id: str, model_name: str) -> dict:
    """Scrape structured specs from joola.com.br product page."""
    specs = {"paddle_id": paddle_id, "model_name": model_name, "url": url, "source": "joola.com.br"}

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)

        # Click "Especificação" tab
        tab_selectors = [
            'text=Especificação',
            'text=Especificações',
            '.tabs-nav__item:has-text("Especificação")',
            'button:has-text("Especificação")',
            '[role="tab"]:has-text("Especificação")',
        ]

        tab_clicked = False
        for sel in tab_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2000):
                    await el.click()
                    await asyncio.sleep(1)
                    tab_clicked = True
                    break
            except Exception:
                continue

        if not tab_clicked:
            # Try scrolling down to find the tab
            await page.mouse.wheel(0, 800)
            await asyncio.sleep(1)
            for sel in tab_selectors:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=1000):
                        await el.click()
                        await asyncio.sleep(1)
                        tab_clicked = True
                        break
                except Exception:
                    continue

        # Extract structured metafield rows
        rows = await page.query_selector_all('.metafield-row')
        raw_specs = {}
        for row in rows:
            label_el = await row.query_selector('.metafield-label')
            value_el = await row.query_selector('.metafield-value')
            if label_el and value_el:
                label = (await label_el.inner_text()).strip().lower()
                value = (await value_el.inner_text()).strip()
                raw_specs[label] = value

        # Map structured data to our schema
        for label, value in raw_specs.items():
            if any(k in label for k in ['superfície', 'surface', 'face']):
                fm = map_face_material(value)
                if fm:
                    specs['face_material'] = fm
            elif any(k in label for k in ['espessura', 'core', 'thickness']):
                mm = extract_mm(value)
                if mm:
                    specs['core_thickness_mm'] = mm
            elif any(k in label for k in ['peso', 'weight']):
                g = extract_weight_g(value)
                if g:
                    specs['weight_grams'] = g
            elif any(k in label for k in ['comprimento da raquete', 'paddle length', 'comprimento']):
                cm = extract_cm(value)
                if cm:
                    specs['paddle_length_cm'] = cm
            elif any(k in label for k in ['largura', 'paddle width', 'width']):
                cm = extract_cm(value)
                if cm:
                    specs['paddle_width_cm'] = cm
            elif any(k in label for k in ['circunferência do grip', 'grip circumference', 'grip circunferência']):
                cm = extract_cm(value)
                if cm:
                    specs['grip_circumference'] = f"{cm}"
            elif any(k in label for k in ['comprimento do grip', 'grip length', 'grip comprimento', 'handle']):
                cm = extract_cm(value)
                if cm:
                    specs['handle_length'] = f"{cm}"
            elif any(k in label for k in ['tecnologia', 'technology', 'core technology']):
                cm_val = map_core_material(value)
                if cm_val:
                    specs['core_material'] = cm_val

        # Fallback: try to extract from full page text if no metafields found
        if len(specs) <= 4:
            text = await page.inner_text('body')
            specs = {**specs, **parse_freetext_specs(text)}

        has_data = len([k for k in specs if k not in ('paddle_id', 'model_name', 'url', 'source')]) > 0
        status = "✅" if has_data else "⚠️ "
        print(f"  {status} [Joola] {model_name}: {len(specs) - 4} fields")

    except Exception as e:
        print(f"  ❌ [Joola] {model_name}: {e}")

    return specs


# ─── BR Pickleball Store Scraper ──────────────────────────────────────────────

async def scrape_bps_page(page, url: str, paddle_id: str, model_name: str) -> dict:
    """Scrape text-based specs from brazilpickleballstore.com.br."""
    specs = {"paddle_id": paddle_id, "model_name": model_name, "url": url, "source": "brazilpickleballstore.com.br"}

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)

        # Try to get the description text
        desc_text = ""
        for selector in ['.user-content', '.product-description', '#description', '.description']:
            try:
                el = page.locator(selector).first
                if await el.is_visible(timeout=2000):
                    desc_text = await el.inner_text()
                    break
            except Exception:
                continue

        if not desc_text:
            # Fallback: get all body text
            desc_text = await page.inner_text('body')

        parsed = parse_freetext_specs(desc_text)
        specs.update(parsed)

        has_data = len([k for k in specs if k not in ('paddle_id', 'model_name', 'url', 'source')]) > 0
        status = "✅" if has_data else "⚠️ "
        print(f"  {status} [BPS] {model_name}: {len(specs) - 4} fields")

    except Exception as e:
        print(f"  ❌ [BPS] {model_name}: {e}")

    return specs


# ─── Free Text Parser ─────────────────────────────────────────────────────────

def parse_freetext_specs(text: str) -> dict:
    """Extract specs from unstructured Portuguese product description."""
    specs = {}
    t = text.lower()

    # Core thickness
    mm = extract_mm(text)
    if mm and 10 <= mm <= 20:
        specs['core_thickness_mm'] = mm

    # Face material
    for keyword, material in FACE_MATERIAL_MAP.items():
        if keyword in t:
            specs['face_material'] = material
            break

    # Core material
    for keyword, material in CORE_MATERIAL_MAP.items():
        if keyword in t:
            specs['core_material'] = material
            break

    # Shape detection
    for keyword, shape in SHAPE_MAP.items():
        if keyword in t:
            specs['shape'] = shape
            break

    # Weight
    w = extract_weight_g(text)
    if w and 150 <= w <= 350:
        specs['weight_grams'] = w

    return specs


# ─── DB Persistence ────────────────────────────────────────────────────────────

def update_paddle_specs(specs: dict, store_slug: str, session) -> bool:
    """
    Write specs to paddle_master if all 4 required fields are present.
    Returns True if paddle was updated, False if skipped.

    Required fields: core_thickness_mm, face_material, weight_grams, shape
    """
    from sqlmodel import Session, select
    from app.db.ingestor import normalize
    from app.models.enums import FaceMaterial, PaddleShape
    from app.models import Brand, PaddleMaster

    required = ['core_thickness_mm', 'face_material', 'weight_grams', 'shape']
    if not all(specs.get(f) is not None for f in required):
        return False

    brand_name = normalize(specs['brand_name'])
    model_name = normalize(specs['model_name'])

    brand = session.exec(select(Brand).where(Brand.name == brand_name)).first()
    if not brand:
        return False

    paddle = session.exec(
        select(PaddleMaster).where(
            PaddleMaster.brand_id == brand.id,
            PaddleMaster.model_name == model_name,
        )
    ).first()
    if not paddle:
        return False

    paddle.core_thickness_mm = specs['core_thickness_mm']
    paddle.face_material = FaceMaterial(specs['face_material'].lower())
    paddle.shape = PaddleShape(specs['shape'].lower())
    paddle.weight_grams = specs['weight_grams']
    paddle.specs_source = "scraping"

    source_key = f"scraping_{store_slug}"
    sources = list(paddle.validation_sources or [])
    if source_key not in sources:
        sources.append(source_key)
    paddle.validation_sources = sources

    session.add(paddle)
    return True


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main(store: str | None = None, dry_run: bool = False):
    from sqlmodel import Session, select
    from app.db.database import sync_engine, init_db_sync
    from app.models import Brand, PaddleMaster
    from app.models.market_offer import MarketOffer


    print("🔍 Scraper Detalhado — Extração de Specs das Lojas BR")
    print("=" * 60)

    init_db_sync()

    with Session(sync_engine) as session:
        if store:
            store_id = STORE_SLUG_TO_ID.get(store)
            if not store_id:
                print(f"Store '{store}' not found.")
                return
            print(f"Store: {store}")
            offers = session.exec(
                select(MarketOffer, PaddleMaster, Brand.name)
                .join(PaddleMaster, MarketOffer.paddle_id == PaddleMaster.id)
                .join(Brand, PaddleMaster.brand_id == Brand.id)
                .where(MarketOffer.store_id == store_id)
                .where(MarketOffer.is_active == True)
            ).all()
        else:
            offers = session.exec(
                select(MarketOffer, PaddleMaster, Brand.name)
                .join(PaddleMaster, MarketOffer.paddle_id == PaddleMaster.id)
                .join(Brand, PaddleMaster.brand_id == Brand.id)
                .where(MarketOffer.is_active == True)
            ).all()

    targets = [(offer, paddle, brand_name) for offer, paddle, brand_name in offers]
    targets_unique = {}
    for offer, paddle, brand_name in targets:
        key = (paddle.id, offer.store_id)
        if key not in targets_unique:
            targets_unique[key] = {
                "paddle_id": str(paddle.id),
                "model_name": paddle.model_name,
                "brand_name": brand_name,
                "url": offer.url,
                "store_id": offer.store_id,
            }

    target_list = list(targets_unique.values())
    print(f"📦 Targets: {len(target_list)} paddles")

    if dry_run:
        print("\n🔎 DRY RUN — URLs that would be scraped:")
        for t in target_list:
            print(f"  {t['brand_name']:10s} | {t['model_name'][:40]:40s} | {t['url'][:60]}")
        return

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 900})
        page = await context.new_page()

        enriched, skipped, errors = 0, 0, 0

        with Session(sync_engine) as session:
            for t in target_list:
                url_slug = store or "unknown"
                if 'joola.com.br' in t['url'] and (not store or store == 'joola'):
                    specs = await scrape_joola_page(page, t['url'], t['paddle_id'], t['model_name'])
                    specs['brand_name'] = t['brand_name']
                    slug = 'joola'
                elif 'brazilpickleballstore' in t['url'] and (not store or store == 'brazil_pickleball_store'):
                    specs = await scrape_bps_page(page, t['url'], t['paddle_id'], t['model_name'])
                    specs['brand_name'] = t['brand_name']
                    slug = 'brazil_pickleball_store'
                else:
                    print(f"  ⚠️ Store for {t['model_name']} not yet implemented")
                    skipped += 1
                    await asyncio.sleep(0.5)
                    continue

                if update_paddle_specs(specs, slug, session):
                    enriched += 1
                else:
                    skipped += 1

                await asyncio.sleep(1)

            session.commit()

        await browser.close()

    print(f"\n{'=' * 60}")
    print(f"✅ SCRAPING COMPLETE")
    print(f"   🟢 Paddles enriched:  {enriched}")
    print(f"   🔴 Paddles skipped:  {skipped}")
    print(f"   ⚠️  Errors:           {errors}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--store", type=str, help="Store slug to enrich (e.g., joola, brazil_pickleball_store)")
    args = parser.parse_args()
    asyncio.run(main(store=args.store, dry_run=args.dry_run))
