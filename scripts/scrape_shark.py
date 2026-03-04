"""
Scraper: Shark Beach Tennis (WooCommerce)
Domain: sharkbeachtennis.com.br
Output: data/raw/shark.csv
"""
from scraper_utils import fetch_woocommerce_products, save_to_csv

DOMAIN = "sharkbeachtennis.com.br"
STORE = "Shark"
CATEGORY = "pickleball/raquetes-pickleball"
OUTPUT = "data/raw/shark.csv"

def main():
    print(f"🏓 Scraping {STORE}...")
    products = fetch_woocommerce_products(DOMAIN, CATEGORY)
    print(f"  📦 {len(products)} products found")

    rows = []
    for p in products:
        # Shark title sometimes starts with "Raquete de Pickleball Shark ..."
        rows.append({
            "brand_name": "Shark",
            "model_name": p["model"],
            "price_brl": p["price_brl"],
            "product_url": p["product_url"],
            "store_name": STORE,
            "image_url": p["image_url"],
        })
        print(f"  ✅ Shark — {p['model']} — R$ {p['price_brl']:.2f}")

    save_to_csv(rows, OUTPUT)

if __name__ == "__main__":
    main()
