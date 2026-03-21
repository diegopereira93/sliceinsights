"""
Scraper: Joola Brasil (Shopify API)
Domain: joola.com.br
"""
from sqlmodel import Session, select
from scripts.scraper_utils import fetch_shopify_products, shopify_product_to_row
from app.db.database import sync_engine, init_db_sync
from app.db.ingestor import ingest_rows
from app.models.store import Store

DOMAIN = "joola.com.br"
STORE_NAME = "Joola Brasil"
FILTER = ["raquete", "paddle"]


def main():
    print(f"🏓 Scraping {STORE_NAME}...")
    products = fetch_shopify_products(DOMAIN, FILTER)
    print(f"  📦 {len(products)} paddle products found")

    rows = []
    for p in products:
        brand = "Joola"
        model = p["title"].replace("JOOLA", "").replace("Joola", "").strip()
        row = shopify_product_to_row(p, DOMAIN, STORE_NAME, brand, model)
        if row:
            rows.append(row)
            print(f"  ✅ {brand} — {model} — R$ {row['price_brl']:.2f}")

    init_db_sync()
    with Session(sync_engine) as session:
        store = session.exec(select(Store).where(Store.name == STORE_NAME)).one()
        result = ingest_rows(rows, store_id=store.id, session=session)
        session.commit()
    print(f"  Ingested: {result}")


if __name__ == "__main__":
    main()
