"""
Scraper: yoSports (Shopify)
Domain: yosports.com.br
"""
from sqlmodel import Session, select
from scripts.scraper_utils import fetch_shopify_products, shopify_product_to_row, parse_brand_model
from app.db.database import sync_engine, init_db_sync
from app.db.ingestor import ingest_rows
from app.models.store import Store

DOMAIN = "yosports.com.br"
STORE_NAME = "yoSports"
CATEGORY_FILTER = ["pickleball"]


def main():
    print(f"🏓 Scraping {STORE_NAME}...")
    products = fetch_shopify_products(DOMAIN, CATEGORY_FILTER)
    print(f"  📦 {len(products)} products found in API")

    rows = []
    for p in products:
        title = p["title"].lower()
        if "raquete" in title and ("beach" in title or "tennis" in title or "tenis" in title or "badminton" in title):
             if "pickleball" not in title:
                 continue
        
        brand, model = parse_brand_model(p["title"])
        
        tags = " ".join(p.get("tags", [])).lower()
        if "acessório" in tags or "bola" in tags:
            continue
            
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
