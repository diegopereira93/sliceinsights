import asyncio
from sqlmodel import Session, select
from scripts.scraper_utils import fetch_dynamic_products
from app.db.database import sync_engine, init_db_sync
from app.db.ingestor import ingest_rows
from app.models.store import Store

STORE_NAME = "Drop Shot Brasil"
URL = "https://www.dropshot.com.br/produtos?q=pickleball"


async def main():
    print(f"🏓 Scraping {STORE_NAME}...")
    selectors = {
        "container": ".product-link",
        "title": "p",
        "price": "span",
        "link": "",
        "image": "img"
    }
    products = await fetch_dynamic_products(URL, selectors, STORE_NAME, wait_time=8)
    print(f"  📦 {len(products)} paddle products found")

    init_db_sync()
    with Session(sync_engine) as session:
        store = session.exec(select(Store).where(Store.name == STORE_NAME)).one()
        result = ingest_rows(products, store_id=store.id, session=session)
        session.commit()
    print(f"  Ingested: {result}")


if __name__ == "__main__":
    asyncio.run(main())
