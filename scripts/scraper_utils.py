"""
Shared utilities for BR store scrapers.
Shopify API helper + brand/model parsing + CSV output.
"""
import re
import csv
import time
import asyncio
import requests
from pathlib import Path
from typing import Optional


# --- Shopify API ---

def fetch_shopify_products(domain: str, category_filter: list[str]) -> list[dict]:
    """Fetch all products from a Shopify store's public API."""
    all_products = []
    page = 1
    while True:
        r = requests.get(
            f"https://{domain}/products.json",
            params={"limit": 250, "page": page},
            timeout=15,
            headers={"User-Agent": "SliceInsights Catalog Bot 1.0"},
        )
        if r.status_code != 200:
            print(f"  ⚠️  {domain}: HTTP {r.status_code}")
            break
        products = r.json().get("products", [])
        if not products:
            break
        for p in products:
            tags = " ".join(p.get("tags", [])).lower()
            ptype = p.get("product_type", "").lower()
            title = p["title"].lower()
            combined = f"{tags} {ptype} {title}"
            if any(kw in combined for kw in category_filter):
                all_products.append(p)
        page += 1
        time.sleep(0.5)
    return all_products


def shopify_product_to_row(
    p: dict, domain: str, store_name: str, brand: str, model: str
) -> Optional[dict]:
    """Convert Shopify product JSON to output row."""
    available_variants = [v for v in p.get("variants", []) if v.get("available")]
    if not available_variants:
        return None
    price = min(float(v["price"]) for v in available_variants)
    image = p["images"][0]["src"] if p.get("images") else ""
    url = f"https://{domain}/products/{p['handle']}"
    return {
        "brand_name": brand,
        "model_name": model,
        "price_brl": price,
        "product_url": url,
        "store_name": store_name,
        "image_url": image,
    }


# --- Brand / Model parsing ---

KNOWN_BRANDS = [
    "Selkirk", "SLK", "Engage", "Joola", "Drop Shot",
    "Head", "Starvie", "Adidas", "Hyperlight", "Shark",
    "ProKennex", "Wilson", "Onix", "Franklin", "CRBN",
    "Paddletek", "Diadem", "Gamma", "Gearbox", "Electrum",
    "Vatic", "Vulcan", "11six24", "3rdshot", "Spartus",
    "Bread & Butter", "Bread and Butter", "B&B", "Ronbus",
    "Six Zero", "SixZero", "Volair", "Babolat", "Legacy",
]


def parse_brand_model(title: str) -> tuple[str, str]:
    """Extract brand and model from product title."""
    title = re.sub(
        r"^(?:raquete|kit|paddle)\s+(?:de\s+)?(?:pickleball\s+)?",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
    title_lower = title.lower()
    for brand in sorted(KNOWN_BRANDS, key=len, reverse=True):
        if title_lower.startswith(brand.lower()):
            model = title[len(brand):].strip()
            model = re.sub(r"\s+\d+mm$", "", model).strip()
            return brand, model if model else title
    parts = title.split(None, 1)
    return parts[0].title(), parts[1].strip() if len(parts) > 1 else ""


# --- CSV output ---

CSV_COLUMNS = ["brand_name", "model_name", "price_brl", "product_url", "store_name", "image_url"]


# --- Nuvemshop / TiendaNube HTML Scraping ---

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def fetch_html_products(
    domain: str, category_path: str, selectors: dict, store_name: str
) -> list[dict]:
    """
    Generic HTML scraper using BeautifulSoup.
    'selectors' dict example:
    {
        "container": "li.product",
        "title": "h2",
        "price": ".price",
        "link": "a",
        "image": "img"
    }
    """
    from bs4 import BeautifulSoup

    all_products = []
    page = 1
    while True:
        url = f"https://{domain}/{category_path}"
        if "?" in category_path:
            url += f"&page={page}"
        else:
            url += f"?page={page}"
        
        try:
            r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            if r.status_code != 200:
                break
        except Exception as e:
            print(f"  ⚠️  {domain} page {page}: {e}")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(selectors["container"])
        if not cards:
            break

        for card in cards:
            try:
                title_el = card.select_one(selectors["title"])
                title = title_el.get_text(strip=True) if title_el else ""

                link_el = card.select_one(selectors["link"])
                product_url = ""
                if link_el:
                    href = link_el.get("href", "")
                    product_url = (
                        href if href.startswith("http") else f"https://{domain}{href}"
                    )

                price_el = card.select_one(selectors["price"])
                price_brl = 0.0
                if price_el:
                    price_text = price_el.get_text(strip=True)
                    price_match = re.search(r"[\d]+[.,][\d]+[.,]?\d*", price_text)
                    if price_match:
                        raw = price_match.group()
                        if "," in raw:
                            raw = raw.replace(".", "").replace(",", ".")
                        price_brl = float(raw)

                img_el = card.select_one(selectors["image"])
                image_url = ""
                if img_el:
                    image_url = (
                        img_el.get("data-src")
                        or img_el.get("data-lazy-src")
                        or img_el.get("src")
                        or ""
                    )
                    if image_url.startswith("//"):
                        image_url = f"https:{image_url}"

                if title and price_brl > 0:
                    brand, model = parse_brand_model(title)
                    all_products.append({
                        "brand_name": brand,
                        "model_name": model,
                        "price_brl": price_brl,
                        "product_url": product_url,
                        "store_name": store_name,
                        "image_url": image_url,
                    })
            except Exception:
                continue

        page += 1
        time.sleep(1.0) # Respectful delay

    return all_products


async def fetch_dynamic_products(
    url: str, selectors: dict, store_name: str, slow_mo: int = 500, wait_time: int = 5
) -> list[dict]:
    """
    Dynamic HTML scraper using Playwright for JS-heavy or WAF-protected sites.
    """
    from playwright.async_api import async_playwright

    all_products = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=slow_mo)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            extra_http_headers={
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            }
        )
        page = await context.new_page()
        
        print(f"  🌐  Navigating to {url}...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for content or bypass WAF
            await asyncio.sleep(wait_time)
            
            # Wait for container
            try:
                await page.wait_for_selector(selectors["container"], timeout=15000)
            except Exception:
                print(f"  ⚠️  Timeout waiting for {selectors['container']}")
                # Try to take a screenshot for debugging if needed (local only)
                # await page.screenshot(path="debug_scrape.png")
                return []

            # Scroll to load lazy content
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

            cards = await page.query_selector_all(selectors["container"])
            print(f"  📦  Found {len(cards)} items with selector {selectors['container']}")

            for card in cards:
                try:
                    title = ""
                    if selectors["title"].startswith("["): # Attribute selector
                        attr = selectors["title"].strip("[]")
                        title = await card.get_attribute(attr)
                    else:
                        title_el = await card.query_selector(selectors["title"])
                        title = await title_el.inner_text() if title_el else ""

                    # Handle case where card itself is the link or contains the link
                    link_el = await card.query_selector(selectors["link"]) if selectors["link"] else None
                    product_url = ""
                    if link_el:
                        href = await link_el.get_attribute("href")
                        if href:
                            product_url = href if href.startswith("http") else f"https://{url.split('/')[2]}{href}"
                    else:
                        # Check if card is an <a> tag
                        if await card.evaluate("node => node.tagName === 'A'"):
                            href = await card.get_attribute("href")
                            if href:
                                product_url = href if href.startswith("http") else f"https://{url.split('/')[2]}{href}"

                    price_el = await card.query_selector(selectors["price"])
                    price_text = ""
                    if price_el:
                        price_text = await price_el.inner_text()
                    else:
                        # Fallback: search in the whole card text
                        price_text = await card.inner_text()

                    price_brl = 0.0
                    if price_text:
                        price_match = re.search(r"(?:R\$|R\s?\$)\s?([\d.]+,\d{2})", price_text)
                        if not price_match:
                             price_match = re.search(r"[\d]+[.,][\d]+[.,]?\d*", price_text)
                        
                        if price_match:
                            raw = price_match.group(1) if price_match.groups() else price_match.group()
                            if "," in raw:
                                raw = raw.replace(".", "").replace(",", ".")
                            try:
                                price_brl = float(raw)
                            except ValueError:
                                pass

                    img_el = await card.query_selector(selectors["image"])
                    image_url = ""
                    if img_el:
                        image_url = (await img_el.get_attribute("src") 
                                     or await img_el.get_attribute("data-src") or "")
                        if image_url.startswith("//"):
                            image_url = f"https:{image_url}"
                        elif image_url.startswith("/") and not image_url.startswith("//"):
                             image_url = f"https://{url.split('/')[2]}{image_url}"

                    if title and price_brl > 0:
                        brand, model = parse_brand_model(title)
                        all_products.append({
                            "brand_name": brand,
                            "model_name": model,
                            "price_brl": price_brl,
                            "product_url": product_url,
                            "store_name": store_name,
                            "image_url": image_url,
                        })
                except Exception as e:
                    # print(f"  ⚠️  Error parsing card: {e}")
                    continue
        except Exception as e:
            print(f"  ⚠️  Navigation error: {e}")
        finally:
            await browser.close()
    return all_products


def fetch_nuvemshop_products(domain: str, category_path: str) -> list[dict]:
    """Scrape product data from Nuvemshop/TiendaNube stores via HTML."""
    from bs4 import BeautifulSoup

    all_products = []
    page = 1
    while True:
        url = f"https://{domain}/{category_path}?page={page}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            if r.status_code != 200:
                break
        except Exception as e:
            print(f"  ⚠️  {domain} page {page}: {e}")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".js-item-product, .item-product, [data-product-id]")
        if not cards:
            break

        for card in cards:
            try:
                title_el = card.select_one(".js-item-name, .item-name, h2 a, h3 a, .product-item-name")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                link_el = card.select_one("a[href]")
                product_url = ""
                if link_el:
                    href = link_el.get("href", "")
                    product_url = href if href.startswith("http") else f"https://{domain}{href}"

                price_el = card.select_one(
                    ".js-price-display, .item-price, .price, [data-product-price]"
                )
                price_brl = 0.0
                if price_el:
                    price_text = price_el.get_text(strip=True)
                    price_match = re.search(r"[\d]+[.,][\d]+[.,]?\d*", price_text)
                    if price_match:
                        raw = price_match.group()
                        # Handle BR format: "1.889,00" → 1889.00
                        if "," in raw:
                            raw = raw.replace(".", "").replace(",", ".")
                        price_brl = float(raw)

                img_el = card.select_one("img")
                image_url = ""
                if img_el:
                    image_url = (
                        img_el.get("data-srcset", "").split(",")[-1].split()[0]
                        or img_el.get("data-src", "")
                        or img_el.get("src", "")
                    )
                    if image_url.startswith("//"):
                        image_url = f"https:{image_url}"

                if title and price_brl > 0:
                    brand, model = parse_brand_model(title)
                    all_products.append({
                        "title": title,
                        "brand": brand,
                        "model": model,
                        "price_brl": price_brl,
                        "product_url": product_url,
                        "image_url": image_url,
                    })
            except Exception:
                continue

        page += 1
        time.sleep(0.5)

    return all_products


def fetch_woocommerce_products(domain: str, category_path: str) -> list[dict]:
    """Scrape product data from WooCommerce stores via HTML."""
    from bs4 import BeautifulSoup

    all_products = []
    page = 1
    while True:
        url = f"https://{domain}/{category_path}/page/{page}/" if page > 1 else f"https://{domain}/{category_path}/"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            if r.status_code != 200:
                break
        except Exception as e:
            print(f"  ⚠️  {domain} page {page}: {e}")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select("li.product, .product-item")
        if not items:
            break

        for li in items:
            try:
                title_el = li.select_one(
                    "h2.woocommerce-loop-product__title, .product-title, h2 a, h3 a"
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                link_el = li.select_one("a[href]")
                product_url = link_el["href"] if link_el else ""

                price_el = li.select_one(
                    ".price ins .amount, .price .amount, .woocommerce-Price-amount"
                )
                price_brl = 0.0
                if price_el:
                    price_text = price_el.get_text(strip=True)
                    price_match = re.search(r"[\d]+[.,][\d]+[.,]?\d*", price_text)
                    if price_match:
                        raw = price_match.group()
                        if "," in raw:
                            raw = raw.replace(".", "").replace(",", ".")
                        price_brl = float(raw)

                img_el = li.select_one("img")
                image_url = ""
                if img_el:
                    image_url = img_el.get("data-src") or img_el.get("src") or ""

                if title and price_brl > 0:
                    brand, model = parse_brand_model(title)
                    all_products.append({
                        "title": title,
                        "brand": brand,
                        "model": model,
                        "price_brl": price_brl,
                        "product_url": product_url,
                        "image_url": image_url,
                    })
            except Exception:
                continue

        page += 1
        time.sleep(0.5)

    return all_products


PROJECT_ROOT = Path(__file__).resolve().parent.parent


# --- SLO Validation hook ---

def finish_run(scraper_name: str) -> None:
    """Call after a scraper successfully commits data to the database.

    Triggers real-time SLO validation for *scraper_name* and writes the
    result to slo_logs.  This is intentionally non-blocking — any exception
    inside validate_job_slo is caught and logged so that scraper success is
    never dependent on the SLO check.
    """
    print(f"[SLO] SLO validation triggered for {scraper_name}")
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from scripts.slo_validator import validate_job_slo
        validate_job_slo(scraper_name)
    except Exception as exc:
        print(f"[SLO] WARNING: SLO validation failed (non-blocking): {exc}")


def save_to_csv(rows: list[dict], output_path: str) -> None:
    """Save scraped rows to CSV. Path is relative to project root."""
    path = PROJECT_ROOT / output_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✅ {len(rows)} products saved to {path}")
