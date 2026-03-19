"""
Scraper: Joola Brasil (Shopify API)
Domain: joola.com.br
Output: data/raw/joola_brazil.csv
"""
from scripts.scraper_utils import (
    fetch_shopify_products,
    shopify_product_to_row,
    save_to_csv,
)

DOMAIN = "joola.com.br"
STORE = "Joola Brasil"
FILTER = ["raquete", "paddle"]
OUTPUT = "data/raw/joola_brazil.csv"


def main():
    print(f"🏓 Scraping {STORE}...")
    products = fetch_shopify_products(DOMAIN, FILTER)
    print(f"  📦 {len(products)} paddle products found")

    rows = []
    for p in products:
        brand = "Joola"  # Official Joola store — brand is always Joola
        model = p["title"].replace("JOOLA", "").replace("Joola", "").strip()
        row = shopify_product_to_row(p, DOMAIN, STORE, brand, model)
        if row:
            rows.append(row)
            print(f"  ✅ {brand} — {model} — R$ {row['price_brl']:.2f}")

    save_to_csv(rows, OUTPUT)


if __name__ == "__main__":
    main()
