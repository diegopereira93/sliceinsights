from scripts.scraper_utils import fetch_html_products, save_to_csv

DOMAIN = "www.lojasupremo.com.br"
STORE = "Loja Supremo"
CATEGORY = "pickleball/raquetes-pickleball"
OUTPUT = "data/raw/loja_supremo.csv"

def main():
    print(f"🏓 Scraping {STORE}...")
    selectors = {
        "container": ".js-item-product",
        "title": ".js-item-name",
        "price": ".js-price-display",
        "link": "a",
        "image": "img"
    }
    products = fetch_html_products(DOMAIN, CATEGORY, selectors, STORE)
    print(f"  📦 {len(products)} products found")
    
    save_to_csv(products, OUTPUT)

if __name__ == "__main__":
    main()
