"""
Scraper: Loja Supremo (Nuvemshop)
Domain: lojasupremo.com.br
Output: data/raw/loja_supremo.csv
"""
from scraper_utils import fetch_nuvemshop_products, save_to_csv

DOMAIN = "www.lojasupremo.com.br"
STORE = "Loja Supremo"
CATEGORY = "pickleball/raquetes-pickleball"
OUTPUT = "data/raw/loja_supremo.csv"

def main():
    print(f"🏓 Scraping {STORE}...")
    # Loja Supremo uses 'pickleball' as main category for Diadem
    products = fetch_nuvemshop_products(DOMAIN, CATEGORY)
    print(f"  📦 {len(products)} products found")

    rows = []
    for p in products:
        # Basic filtering to ensure it's a paddle
        if "bola" in p["title"].lower() or "raqueteira" in p["title"].lower():
            continue
            
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
