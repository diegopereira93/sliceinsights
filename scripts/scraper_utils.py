"""
Shared utilities for BR store scrapers.
Shopify API helper + brand/model parsing + CSV output.
"""
import re
import csv
import time
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
    "Vatic", "Vulcan", "11six24", "3rdshot",
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

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}


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


def save_to_csv(rows: list[dict], output_path: str) -> None:
    """Save scraped rows to CSV. Path is relative to project root."""
    path = PROJECT_ROOT / output_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✅ {len(rows)} products saved to {path}")
