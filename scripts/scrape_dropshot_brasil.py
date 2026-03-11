import asyncio
from scraper_utils import fetch_dynamic_products, save_to_csv

STORE = "Drop Shot Brasil"
OUTPUT = "data/raw/dropshot_brasil_products.csv"
URL = "https://www.dropshot.com.br/produtos?q=pickleball"

async def main():
    print(f"🏓 Scraping {STORE}...")
    selectors = {
        "container": ".product-link",
        "title": "p",
        "price": "span",
        "link": "", # Card is the link
        "image": "img"
    }
    products = await fetch_dynamic_products(URL, selectors, STORE, wait_time=8)
    print(f"  📦 {len(products)} paddle products found")
    
    save_to_csv(products, OUTPUT)

if __name__ == "__main__":
    asyncio.run(main())
