"""
Scraper: ProPadel (HTML scraping)
Domain: lojapropadel.com.br

NOTE: Filter for pickleball products only — this store also sells padel equipment.
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from sqlmodel import Session, select
from scripts.scraper_utils import parse_brand_model
from app.db.database import sync_engine, init_db_sync
from app.db.ingestor import ingest_rows
from app.models.store import Store

DOMAIN = "www.lojapropadel.com.br"
STORE_NAME = "ProPadel"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

PICKLEBALL_KEYWORDS = ["pickleball", "pickle"]


def scrape_category(category_path: str) -> list[dict]:
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
            ".product-item, li.product, [data-product-id], "
            ".js-item-product, .card-product"
        )
        if not items:
            break

        for item in items:
            try:
                title_el = item.select_one("h2, h3, .product-title, .js-item-name, a[title]")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                combined = title.lower()
                tags_el = item.get("data-tags", "")
                combined += f" {tags_el}".lower()
                if not any(kw in combined for kw in PICKLEBALL_KEYWORDS):
                    continue

                link_el = item.select_one("a[href]")
                product_url = ""
                if link_el:
                    href = link_el.get("href", "")
                    product_url = href if href.startswith("http") else f"https://{DOMAIN}{href}"

                price_el = item.select_one(".price, [data-product-price]")
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
                    all_products.append({
                        "brand_name": brand,
                        "model_name": model,
                        "price_brl": price_brl,
                        "product_url": product_url,
                        "image_url": image_url,
                    })
            except Exception:
                continue

        page += 1
        time.sleep(0.5)

    return all_products


def main():
    print(f"🏓 Scraping {STORE_NAME}...")
    rows = []
    for path in ["pickleball", "raquetes-pickleball", "raquetes", "colecao/pickleball"]:
        result = scrape_category(path)
        if result:
            rows.extend(result)
            break

    print(f"  📦 {len(rows)} paddle products found")
    for r in rows:
        print(f"  ✅ {r['brand_name']} — {r['model_name']} — R$ {r['price_brl']:.2f}")

    init_db_sync()
    with Session(sync_engine) as session:
        store = session.exec(select(Store).where(Store.name == STORE_NAME)).one()
        result = ingest_rows(rows, store_id=store.id, session=session)
        session.commit()
    print(f"  Ingested: {result}")


if __name__ == "__main__":
    main()
