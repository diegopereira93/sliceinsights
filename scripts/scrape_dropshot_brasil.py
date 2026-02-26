"""
Scraper: Drop Shot Brasil (HTML scraping)
Domain: dropshot.com.br
Output: data/raw/dropshot_brasil_products.csv
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from scraper_utils import parse_brand_model, save_to_csv

DOMAIN = "www.dropshot.com.br"
STORE = "Drop Shot Brasil"
OUTPUT = "data/raw/dropshot_brasil_products.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}


def scrape_category(category_path: str) -> list[dict]:
    """Scrape a category page for pickleball products."""
    all_products = []
    page = 1
    while True:
        url = f"https://{DOMAIN}/{category_path}" + (f"?page={page}" if page > 1 else "")
        try:
            r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            if r.status_code != 200:
                break
        except Exception as e:
            print(f"  ⚠️  Page {page}: {e}")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select(
            ".product-item, .producto-item, li.product, "
            "[data-product-id], .js-item-product, .card-product"
        )
        if not items:
            break

        for item in items:
            try:
                title_el = item.select_one("h2, h3, .product-title, .js-item-name, a[title]")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                link_el = item.select_one("a[href]")
                product_url = ""
                if link_el:
                    href = link_el.get("href", "")
                    product_url = href if href.startswith("http") else f"https://{DOMAIN}{href}"

                price_el = item.select_one(".price, .producto-price, [data-product-price]")
                price_brl = 0.0
                if price_el:
                    price_text = price_el.get_text(strip=True)
                    match = re.search(r"[\d]+[.,][\d]+[.,]?\d*", price_text)
                    if match:
                        raw = match.group()
                        if "," in raw:
                            raw = raw.replace(".", "").replace(",", ".")
                        price_brl = float(raw)

                img_el = item.select_one("img")
                image_url = ""
                if img_el:
                    image_url = img_el.get("data-src") or img_el.get("src") or ""
                    if image_url.startswith("//"):
                        image_url = f"https:{image_url}"

                if title and price_brl > 0:
                    brand, model = parse_brand_model(title)
                    if brand.lower() in ("drop", "raquete"):
                        brand = "Drop Shot"
                        model = title.replace("Drop Shot", "").strip()
                    all_products.append({
                        "brand_name": brand,
                        "model_name": model,
                        "price_brl": price_brl,
                        "product_url": product_url,
                        "store_name": STORE,
                        "image_url": image_url,
                    })
            except Exception:
                continue

        page += 1
        time.sleep(0.5)

    return all_products


def main():
    print(f"🏓 Scraping {STORE}...")
    # Try common category paths for pickleball
    rows = []
    for path in ["pickleball", "raquetes-pickleball", "raquetes", "colecao/pickleball"]:
        result = scrape_category(path)
        if result:
            rows.extend(result)
            break

    print(f"  📦 {len(rows)} paddle products found")
    for r in rows:
        print(f"  ✅ {r['brand_name']} — {r['model_name']} — R$ {r['price_brl']:.2f}")

    save_to_csv(rows, OUTPUT)


if __name__ == "__main__":
    main()
