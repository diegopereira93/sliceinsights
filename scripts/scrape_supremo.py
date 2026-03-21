from sqlmodel import Session, select
from scripts.scraper_utils import fetch_html_products
from app.db.database import sync_engine, init_db_sync
from app.db.ingestor import ingest_rows
from app.models.store import Store

DOMAIN = "www.lojasupremo.com.br"
STORE_NAME = "Loja Supremo"
CATEGORY = "pickleball/raquetes-pickleball"


def main():
    print(f"🏓 Scraping {STORE_NAME}...")
    selectors = {
        "container": ".js-item-product",
        "title": ".js-item-name",
        "price": ".js-price-display",
        "link": "a",
        "image": "img"
    }
    products = fetch_html_products(DOMAIN, CATEGORY, selectors, STORE_NAME)
    print(f"  📦 {len(products)} products found")

    init_db_sync()
    with Session(sync_engine) as session:
        store = session.exec(select(Store).where(Store.name == STORE_NAME)).one()
        result = ingest_rows(products, store_id=store.id, session=session)
        session.commit()
    print(f"  Ingested: {result}")


if __name__ == "__main__":
    main()
