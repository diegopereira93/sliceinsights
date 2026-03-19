"""
Scraper: PCKL House (Nuvemshop/TiendaNube)
Domain: pcklhouse.com.br
Output: data/raw/pcklhouse_products.csv
"""
from scripts.scraper_utils import fetch_nuvemshop_products, save_to_csv

DOMAIN = "www.pcklhouse.com.br"
STORE = "PCKL House"
CATEGORY = "raquetes"
OUTPUT = "data/raw/pcklhouse_products.csv"


def main():
    print(f"🏓 Scraping {STORE}...")
    # Try common Nuvemshop category paths
    products = fetch_nuvemshop_products(DOMAIN, CATEGORY)
    if not products:
        for alt in ["raquete", "pickleball", "produtos"]:
            products = fetch_nuvemshop_products(DOMAIN, alt)
            if products:
                break

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
