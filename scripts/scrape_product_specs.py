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
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

STORE_SLUG_TO_ID = {
    "joola": 2,
    "brazil_pickleball_store": 1,
    "yosports": 3,
    "supremo": 4,
    "shark": 5,
    "prospin": 6,
    "drop_shot_brasil": 7,
    "just_paddles": 10,
    "pcklhouse": 8,
    "propadel": 9,
}

STORE_HANDLERS = {
    "joola": {"func": "scrape_joola_page", "async": True},
    "brazil_pickleball_store": {"func": "scrape_bps_page", "async": True},
    "yosports": {"func": "scrape_yosports_specs", "async": False},
    "supremo": {"func": "scrape_supremo_specs", "async": False},
    "shark": {"func": "scrape_shark_specs", "async": False},
    "prospin": {"func": "scrape_prospin_specs", "async": False},
    "drop_shot_brasil": {"func": "scrape_drop_shot_specs", "async": True},
    "just_paddles": {"func": "scrape_just_paddles_specs", "async": True},
    "pcklhouse": {"func": "scrape_pcklhouse_specs", "async": False},
    "propadel": {"func": "scrape_propadel_specs", "async": False},
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


# ─── Store Spec Extractors ─────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _fetch_product_page(url: str) -> str | None:
    """Fetch product page HTML. Returns None on failure."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return None


def scrape_yosports_specs(product_url: str, brand_name: str, model_name: str) -> dict:
    """Extract specs from yosports.com.br product page (Shopify, freetext)."""
    specs = {"brand_name": brand_name, "model_name": model_name}
    html = _fetch_product_page(product_url)
    if not html:
        return specs
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        desc = soup.select_one(".product-description, .description, [itemprop='description']")
        if desc:
            text = desc.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)
        parsed = parse_freetext_specs(text)
        specs.update(parsed)
    except Exception:
        pass
    return specs


def scrape_supremo_specs(product_url: str, brand_name: str, model_name: str) -> dict:
    """Extract specs from lojasupremo.com.br product page (Nuvemshop, freetext)."""
    specs = {"brand_name": brand_name, "model_name": model_name}
    html = _fetch_product_page(product_url)
    if not html:
        return specs
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for sel in [".product-description", ".js-product-description", "[itemprop='description']"]:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(separator=" ", strip=True)
                parsed = parse_freetext_specs(text)
                specs.update(parsed)
                break
    except Exception:
        pass
    return specs


def scrape_shark_specs(product_url: str, brand_name: str, model_name: str) -> dict:
    """Extract specs from sharkbeachtennis.com.br (WooCommerce, structured + freetext)."""
    specs = {"brand_name": brand_name, "model_name": model_name}
    html = _fetch_product_page(product_url)
    if not html:
        return specs
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        rows = soup.select("table.woocommerce-product-attributes tr")
        for row in rows:
            label_el = row.select_one("th")
            value_el = row.select_one("td")
            if not label_el or not value_el:
                continue
            label = label_el.get_text(strip=True).lower()
            value = value_el.get_text(strip=True)
            if any(k in label for k in ["espessura", "thickness", "core"]):
                mm = extract_mm(value)
                if mm:
                    specs["core_thickness_mm"] = mm
            elif any(k in label for k in ["superficie", "surface", "face"]):
                fm = map_face_material(value)
                if fm:
                    specs["face_material"] = fm
            elif any(k in label for k in ["peso", "weight"]):
                g = extract_weight_g(value)
                if g:
                    specs["weight_grams"] = g
            elif any(k in label for k in ["formato", "shape"]):
                sh = map_shape(value)
                if sh:
                    specs["shape"] = sh

        if "core_thickness_mm" not in specs:
            for sel in [".woocommerce-product-details__short-description", ".product-description"]:
                el = soup.select_one(sel)
                if el:
                    text = el.get_text(separator=" ", strip=True)
                    parsed = parse_freetext_specs(text)
                    specs.update(parsed)
                    break
    except Exception:
        pass
    return specs


def scrape_prospin_specs(product_url: str, brand_name: str, model_name: str) -> dict:
    """Extract specs from prospin.com.br (WooCommerce, structured + freetext)."""
    specs = {"brand_name": brand_name, "model_name": model_name}
    html = _fetch_product_page(product_url)
    if not html:
        return specs
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        rows = soup.select("table.woocommerce-product-attributes tr")
        for row in rows:
            label_el = row.select_one("th")
            value_el = row.select_one("td")
            if not label_el or not value_el:
                continue
            label = label_el.get_text(strip=True).lower()
            value = value_el.get_text(strip=True)
            if any(k in label for k in ["espessura", "thickness", "core"]):
                mm = extract_mm(value)
                if mm:
                    specs["core_thickness_mm"] = mm
            elif any(k in label for k in ["superficie", "surface", "face"]):
                fm = map_face_material(value)
                if fm:
                    specs["face_material"] = fm
            elif any(k in label for k in ["peso", "weight"]):
                g = extract_weight_g(value)
                if g:
                    specs["weight_grams"] = g
            elif any(k in label for k in ["formato", "shape"]):
                sh = map_shape(value)
                if sh:
                    specs["shape"] = sh

        if "core_thickness_mm" not in specs:
            for sel in [".woocommerce-product-details__short-description", ".product-description"]:
                el = soup.select_one(sel)
                if el:
                    text = el.get_text(separator=" ", strip=True)
                    parsed = parse_freetext_specs(text)
                    specs.update(parsed)
                    break
    except Exception:
        pass
    return specs


def scrape_pcklhouse_specs(product_url: str, brand_name: str, model_name: str) -> dict:
    """Extract specs from pcklhouse.com.br (Nuvemshop, freetext)."""
    specs = {"brand_name": brand_name, "model_name": model_name}
    html = _fetch_product_page(product_url)
    if not html:
        return specs
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for sel in [".product-description", ".js-product-description", "[itemprop='description']"]:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(separator=" ", strip=True)
                parsed = parse_freetext_specs(text)
                specs.update(parsed)
                break
    except Exception:
        pass
    return specs


def scrape_propadel_specs(product_url: str, brand_name: str, model_name: str) -> dict:
    """Extract specs from lojapropadel.com.br (custom HTML, freetext)."""
    specs = {"brand_name": brand_name, "model_name": model_name}
    html = _fetch_product_page(product_url)
    if not html:
        return specs
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for sel in [".product-description", ".description", "[itemprop='description']", ".product-info"]:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(separator=" ", strip=True)
                if text:
                    parsed = parse_freetext_specs(text)
                    specs.update(parsed)
                    break
        if "core_thickness_mm" not in specs:
            text = soup.get_text(separator=" ", strip=True)
            if text:
                parsed = parse_freetext_specs(text)
                specs.update(parsed)
    except Exception:
        pass
    return specs


# ─── Playwright Store Extractors ───────────────────────────────────────────────

async def scrape_drop_shot_specs(page, url: str, brand_name: str, model_name: str) -> dict:
    """Extract specs from dropshot.com.br using Playwright (JS dynamic content)."""
    specs = {"brand_name": brand_name, "model_name": model_name}
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)

        for sel in [".product-description", ".product-specs", "[itemprop='description']"]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=3000):
                    text = await el.inner_text()
                    parsed = parse_freetext_specs(text)
                    specs.update(parsed)
                    break
            except Exception:
                continue

        if "core_thickness_mm" not in specs:
            text = await page.inner_text("body")
            parsed = parse_freetext_specs(text)
            specs.update(parsed)

        has_data = any(specs.get(f) for f in ["core_thickness_mm", "face_material", "weight_grams", "shape"])
        status = "✅" if has_data else "⚠️ "
        print(f"  {status} [DropShot] {model_name}: {sum(1 for f in ['core_thickness_mm','face_material','weight_grams','shape'] if specs.get(f))}/4 fields")
    except Exception as e:
        print(f"  ❌ [DropShot] {model_name}: {e}")
    return specs


async def scrape_just_paddles_specs(page, url: str, brand_name: str, model_name: str) -> dict:
    """Extract specs from justpaddles.com using Playwright (JS dynamic content)."""
    specs = {"brand_name": brand_name, "model_name": model_name}
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)

        for sel in [".product-description", ".product-details", "[itemprop='description']"]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=3000):
                    text = await el.inner_text()
                    parsed = parse_freetext_specs(text)
                    specs.update(parsed)
                    break
            except Exception:
                continue

        if "core_thickness_mm" not in specs:
            text = await page.inner_text("body")
            parsed = parse_freetext_specs(text)
            specs.update(parsed)

        has_data = any(specs.get(f) for f in ["core_thickness_mm", "face_material", "weight_grams", "shape"])
        status = "✅" if has_data else "⚠️ "
        print(f"  {status} [JustPaddles] {model_name}: {sum(1 for f in ['core_thickness_mm','face_material','weight_grams','shape'] if specs.get(f))}/4 fields")
    except Exception as e:
        print(f"  ❌ [JustPaddles] {model_name}: {e}")
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
        id_to_slug = {v: k for k, v in STORE_SLUG_TO_ID.items()}
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
            slug = id_to_slug.get(offer.store_id)
            targets_unique[key] = {
                "paddle_id": str(paddle.id),
                "model_name": paddle.model_name,
                "brand_name": brand_name,
                "url": offer.url,
                "store_id": offer.store_id,
                "store_slug": slug,
            }

    target_list = list(targets_unique.values())
    print(f"📦 Targets: {len(target_list)} paddles")

    if dry_run:
        print("\n🔎 DRY RUN — URLs that would be scraped:")
        for t in target_list:
            print(f"  {t['brand_name']:10s} | {t['model_name'][:40]:40s} | {t['url'][:60]}")
        return

    from playwright.async_api import async_playwright

    stores_to_scrape = [store] if store else list(STORE_HANDLERS.keys())

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 900})
        page = await context.new_page()

        enriched, skipped, errors = 0, 0, 0

        for slug in stores_to_scrape:
            handler_info = STORE_HANDLERS.get(slug)
            if not handler_info:
                print(f"  ⚠️  Store '{slug}' not yet implemented")
                continue

            handler_name = handler_info["func"]
            is_async = handler_info["async"]
            store_targets = [t for t in target_list if t.get("store_slug") == slug or
                             (slug == "joola" and "joola.com.br" in t["url"]) or
                             (slug == "brazil_pickleball_store" and "brazilpickleballstore" in t["url"])]

            if not store_targets:
                continue

            print(f"\n🟢 Scraping {len(store_targets)} paddles from {slug}...")
            handler_func = globals()[handler_name]

            for t in store_targets:
                try:
                    if is_async:
                        specs = await handler_func(page, t["url"], t["brand_name"], t["model_name"])
                    else:
                        specs = handler_func(t["url"], t["brand_name"], t["model_name"])
                    specs["brand_name"] = t["brand_name"]

                    if update_paddle_specs(specs, slug, session):
                        enriched += 1
                    else:
                        skipped += 1

                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"  ❌ [{slug}] {t['model_name']}: {e}")
                    errors += 1

            print(f"  ✅ {slug}: {enriched}/{len(store_targets)} enriched")

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
