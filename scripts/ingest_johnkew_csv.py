"""
Ingest JohnKew CSV data into the Paddle catalog.
Focuses on technical specs like swing_weight, twist_weight, and spin_rpm.
Updates the `validation_sources` field for the affected paddles.

Usage:
  docker compose exec backend_v3 python scripts/ingest_johnkew_csv.py --csv /app/data/johnkew.csv
  docker compose exec backend_v3 python scripts/ingest_johnkew_csv.py --csv /app/data/johnkew.csv --dry-run
"""
import sys
import argparse
from pathlib import Path

import pandas as pd
from sqlmodel import Session, select
from sqlalchemy.orm import attributes

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import sync_engine, init_db_sync
from app.models import Brand, PaddleMaster
from app.models.paddle import calculate_specs_confidence
from scripts.enrich_from_csv import normalize, clean_model, resolve_brands, fuzzy_score, clean_float, clean_int

SOURCE_NAME = "johnkew"

def find_column(df: pd.DataFrame, keywords: list[str]) -> str | None:
    """Find a column in the DataFrame that contains all keywords (case-insensitive)."""
    for col in df.columns:
        col_str = str(col).lower()
        if all(kw in col_str for kw in keywords):
            return col
    return None

def ingest(csv_path: str, dry_run: bool = False):
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"🧠 JohnKew Ingest Pipeline — {csv_path} → PostgreSQL [{mode}]")
    print("=" * 60)

    path = Path(csv_path)
    if not path.exists():
        print(f"❌ CSV not found: {path}")
        return

    df = pd.read_csv(path, on_bad_lines='skip')
    print(f"📦 CSV: {len(df)} rows loaded")

    # Detect Columns
    brand_col = find_column(df, ["brand"])
    model_col = find_column(df, ["model"])
    sw_col = find_column(df, ["swing", "weight"])
    tw_col = find_column(df, ["twist", "weight"])
    spin_col = find_column(df, ["spin"])

    if not brand_col or not model_col:
        print("❌ Could not find Brand and Model columns in the CSV.")
        print(f"Available columns: {df.columns.tolist()}")
        return

    print("📊 Detected Columns:")
    print(f"  Brand: {brand_col}")
    print(f"  Model: {model_col}")
    print(f"  Swing Weight: {sw_col}")
    print(f"  Twist Weight: {tw_col}")
    print(f"  Spin RPM: {spin_col}")

    init_db_sync()

    with Session(sync_engine) as session:
        paddles = session.exec(
            select(PaddleMaster).join(Brand, PaddleMaster.brand_id == Brand.id)
        ).all()
        brands = {b.id: b for b in session.exec(select(Brand)).all()}

        print(f"\n🎾 DB: {len(paddles)} paddles\n")

        # Build CSV lookup: {(brand_norm, model_norm): row}
        csv_lookup = {}
        for _, row in df.iterrows():
            b = normalize(str(row[brand_col]))
            m = clean_model(str(row[model_col]))
            if b and m:
                csv_lookup[(b, m)] = row

        updated_count = 0
        no_match = 0
        match_log = []

        for paddle in paddles:
            brand = brands.get(paddle.brand_id)
            if not brand:
                continue

            brand_norms = resolve_brands(brand.name)
            model_norm = clean_model(paddle.model_name)
            
            csv_row = None
            match_type = ""

            # 1. Exact match
            match_type = "exact"
            for bn in brand_norms:
                csv_row = csv_lookup.get((bn, model_norm))
                if csv_row is not None:
                     break

            # 2. Fuzzy match
            if csv_row is None:
                best_score = 0.0
                best_row = None
                for (cb, cm), row in csv_lookup.items():
                    if cb not in brand_norms:
                        continue
                    s = fuzzy_score(model_norm, cm)
                    if s > best_score and s >= 0.70:  # strict fuzzy for specs
                        best_score = s
                        best_row = row
                if best_row is not None:
                    csv_row = best_row
                    match_type = f"fuzzy({best_score:.2f})"

            if csv_row is None:
                no_match += 1
                continue

            csv_model_display = f"{csv_row[brand_col]} {csv_row[model_col]}"
            match_log.append(f"  ✅ {match_type:15s} [{brand.name}] {paddle.model_name!r}  →  {csv_model_display!r}")

            updates = {}
            sw = clean_int(csv_row[sw_col]) if sw_col else None
            tw = clean_float(csv_row[tw_col]) if tw_col else None
            sr = clean_int(csv_row[spin_col]) if spin_col else None

            # Always update these physics specs if they are empty
            # Alternatively, JohnKew is so precise we might want to overwrite from JohnKew even if present
            # But the requirement says "Updates ONLY NULL fields" usually, let's stick to filling gaps
            if sw and not paddle.swing_weight:
                updates['swing_weight'] = sw
            if tw and not paddle.twist_weight:
                updates['twist_weight'] = tw
            if sr and not paddle.spin_rpm:
                # JohnKew spin RPMs are highly technical
                updates['spin_rpm'] = sr

            # Update validation sources
            current_sources = list(paddle.validation_sources or [])
            if SOURCE_NAME not in current_sources:
                updates['validation_sources'] = current_sources + [SOURCE_NAME]

            if not updates:
                continue

            updated_count += 1
            if not dry_run:
                for field, value in updates.items():
                    setattr(paddle, field, value)
                
                # Flag as updated explicitly to SA
                attributes.flag_modified(paddle, "validation_sources")
                
                # Re-calculate confidence
                paddle.specs_confidence = calculate_specs_confidence(paddle)

        if not dry_run:
            session.commit()

        print("\n".join(match_log))
        print(f"\n{'=' * 60}")
        print(f"✅ JOHNKEW INGESTION {'PREVIEW' if dry_run else 'COMPLETE'}")
        print(f"   🟢 Updated Paddles: {updated_count}")
        print(f"   🔴 No match:        {no_match}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, required=True, help="Path to JohnKew CSV")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to DB")
    args = parser.parse_args()
    ingest(args.csv, dry_run=args.dry_run)
