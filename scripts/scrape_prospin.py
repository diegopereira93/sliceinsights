"""
Scraper: ProSpin (WooCommerce)
Domain: prospin.com.br
"""
from sqlmodel import Session, select
from scripts.scraper_utils import fetch_woocommerce_products
from app.db.database import sync_engine, init_db_sync
from app.db.ingestor import ingest_rows
from app.models.store import Store

DOMAIN = "www.prospin.com.br"
STORE_NAME = "ProSpin"
CATEGORY = "categoria-produto/pickleball"


def main():
    print(f"🏓 Scraping {STORE_NAME}...")
    products = fetch_woocommerce_products(DOMAIN, CATEGORY)
    print(f"  📦 {len(products)} paddle products found")

    rows = []
    for p in products:
        rows.append({
            "brand_name": p["brand"],
            "model_name": p["model"],
            "price_brl": p["price_brl"],
            "product_url": p["product_url"],
            "image_url": p["image_url"],
        })
        print(f"  ✅ {p['brand']} — {p['model']} — R$ {p['price_brl']:.2f}")

    init_db_sync()
    with Session(sync_engine) as session:
        store = session.exec(select(Store).where(Store.name == STORE_NAME)).one()
        result = ingest_rows(rows, store_id=store.id, session=session)
        session.commit()
    print(f"  Ingested: {result}")


if __name__ == "__main__":
    main()
