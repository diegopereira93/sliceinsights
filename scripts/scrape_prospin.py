"""
Scraper: ProSpin (WooCommerce)
Domain: prospin.com.br
Output: data/raw/prospin_products.csv
"""
from scripts.scraper_utils import fetch_woocommerce_products, save_to_csv

DOMAIN = "www.prospin.com.br"
STORE = "ProSpin"
CATEGORY = "categoria-produto/pickleball"
OUTPUT = "data/raw/prospin_products.csv"


def main():
    print(f"🏓 Scraping {STORE}...")
    products = fetch_woocommerce_products(DOMAIN, CATEGORY)
    print(f"  📦 {len(products)} paddle products found")

    rows = []
    for p in products:
        rows.append({
            "brand_name": p["brand"],
            "model_name": p["model"],
            "price_brl": p["price_brl"],
            "product_url": p["product_url"],
            "store_name": STORE,
            "image_url": p["image_url"],
        })
        print(f"  ✅ {p['brand']} — {p['model']} — R$ {p['price_brl']:.2f}")

    save_to_csv(rows, OUTPUT)


if __name__ == "__main__":
    main()
