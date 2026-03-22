"""
Export database tables to portable CSV files in data/db/.
These CSVs are git-tracked and used to seed dev environments.

Usage: python scripts/export_db_to_csv.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.db.database import sync_engine
from app.models.brand import Brand
from app.models.store import Store
from app.models.paddle import PaddleMaster
from app.models.market_offer import MarketOffer


def export_table(session: Session, model_class, file_path: Path, extra_cols: list = None, row_mapper=None):
    rows = session.exec(select(model_class)).all()
    if not rows:
        print(f"  Empty table: {model_class.__tablename__} -> {file_path.name}")
        return 0

    cols = list(model_class.model_fields.keys())
    if extra_cols:
        cols = extra_cols + cols

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            d = row_mapper(row) if row_mapper else {}
            for col in cols:
                if col not in d:
                    val = getattr(row, col, None)
                    if hasattr(val, "__iter__") and not isinstance(val, str):
                        val = "|".join(str(v) for v in val) if val else ""
                    d[col] = val
            writer.writerow(d)

    return len(rows)


def main():
    db_dir = Path(__file__).parent.parent / "data" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)

    print("Exporting database tables to CSV...")

    with Session(sync_engine) as session:
        n_brands = export_table(session, Brand, db_dir / "brands.csv")
        print(f"  brands.csv: {n_brands} rows")

        n_stores = export_table(session, Store, db_dir / "stores.csv")
        print(f"  stores.csv: {n_stores} rows")

        n_paddles = export_table(
            session, PaddleMaster, db_dir / "paddle_master.csv",
            extra_cols=["brand_name"],
            row_mapper=lambda p: {"brand_name": p.brand.name if p.brand else ""},
        )
        print(f"  paddle_master.csv: {n_paddles} rows")

        n_offers = export_table(
            session, MarketOffer, db_dir / "market_offers.csv",
            extra_cols=["brand_name", "model_name", "store_name"],
            row_mapper=lambda o: {
                "brand_name": o.paddle.brand.name if o.paddle and o.paddle.brand else "",
                "model_name": o.paddle.model_name if o.paddle else "",
                "store_name": o.store.name if o.store else "",
            },
        )
        print(f"  market_offers.csv: {n_offers} rows")

    print(f"\nExported to {db_dir}/")
    for f in sorted(db_dir.glob("*.csv")):
        print(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
