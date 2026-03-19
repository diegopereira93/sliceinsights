"""
Scraper: yoSports (Shopify)
Domain: yosports.com.br
Output: data/raw/yosports.csv
"""
from scripts.scraper_utils import fetch_shopify_products, shopify_product_to_row, save_to_csv, parse_brand_model

DOMAIN = "yosports.com.br"
STORE = "yoSports"
# Strictly pickleball now
CATEGORY_FILTER = ["pickleball"]
OUTPUT = "data/raw/yosports.csv"

def main():
    print(f"🏓 Scraping {STORE}...")
    products = fetch_shopify_products(DOMAIN, CATEGORY_FILTER)
    print(f"  📦 {len(products)} products found in API")

    rows = []
    for p in products:
        title = p["title"].lower()
        # Strict filter to avoid Beach Tennis / Badminton
        if "raquete" in title and ("beach" in title or "tennis" in title or "tenis" in title or "badminton" in title):
             if "pickleball" not in title:
                 continue
        
        # Determine brand and model from title
        brand, model = parse_brand_model(p["title"])
        
        # Filter for known paddle brands or explicit paddle category
        tags = " ".join(p.get("tags", [])).lower()
        if "acessório" in tags or "bola" in tags:
            continue
            
        row = shopify_product_to_row(p, DOMAIN, STORE, brand, model)
        if row:
            rows.append(row)
            print(f"  ✅ {brand} — {model} — R$ {row['price_brl']:.2f}")

    save_to_csv(rows, OUTPUT)

if __name__ == "__main__":
    main()
