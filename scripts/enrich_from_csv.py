"""
P1: Enrich existing paddles with real specs from paddle_stats_dump.csv.
Updates ONLY NULL fields — never overwrites manually entered data.

Run with: docker compose exec backend_v3 python scripts/enrich_from_csv.py
"""
import sys
import re
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd
from sqlmodel import Session, select

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import sync_engine, init_db_sync
from app.models import Brand, PaddleMaster
from app.models.enums import FaceMaterial, PaddleShape

CSV_PATH = Path(__file__).parent.parent / "app" / "data" / "paddle_stats_dump.csv"

# CSV Column mapping (no headers in the CSV)
COL_BRAND = 0
COL_MODEL = 1
COL_PRICE_USD = 2
COL_SWING_WEIGHT = 3
COL_TWIST_WEIGHT = 4
COL_SPIN_RPM = 5
COL_POWER = 6
COL_CORE_MM = 7
COL_HANDLE_LENGTH = 8
COL_GRIP_CIRC = 9
COL_SHAPE = 10
COL_FACE_MATERIAL_1 = 11
COL_FACE_MATERIAL_2 = 12
COL_FACE_MATERIAL_3 = 13
COL_CORE_MATERIAL = 14


def normalize(text: str) -> str:
    if not text or pd.isna(text):
        return ""
    text = str(text).lower().strip()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


NOISE_TOKENS = {'mm', '14mm', '16mm', '13mm', '12mm', '19mm', 'raquete', 'pickleball', 'paddle', 'de'}

def clean_model(text: str) -> str:
    words = normalize(text).split()
    return ' '.join(w for w in words if w not in NOISE_TOKENS)


def clean_float(val) -> float | None:
    if pd.isna(val) or str(val).strip() in ('', 'nan'):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def clean_int(val) -> int | None:
    if pd.isna(val) or str(val).strip() in ('', 'nan'):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def clean_str(val) -> str | None:
    if pd.isna(val) or str(val).strip() in ('', 'nan'):
        return None
    return str(val).strip()


def infer_face_material(name: str) -> FaceMaterial | None:
    n = name.lower()
    if 'kevlar' in n:
        return FaceMaterial.KEVLAR
    if 'fiberglass' in n or 'composite' in n:
        return FaceMaterial.FIBERGLASS
    if 'hybrid' in n:
        return FaceMaterial.HYBRID
    if 'carbon' in n or 'graphite' in n:
        return FaceMaterial.CARBON
    return None


def infer_shape(name: str) -> PaddleShape | None:
    n = name.lower()
    if 'elongated' in n or 'blade' in n:
        return PaddleShape.ELONGATED
    if 'wide' in n or 'widebody' in n:
        return PaddleShape.WIDEBODY
    if 'standard' in n or 'classic' in n:
        return PaddleShape.STANDARD
    return None


def match_score(db_brand: str, db_model: str, csv_brand: str, csv_model: str) -> float:
    """Calculate match score between a DB paddle and a CSV paddle."""
    b1, b2 = normalize(db_brand), normalize(csv_brand)
    if b1 != b2:
        return 0.0

    m1 = clean_model(db_model)
    m2 = clean_model(csv_model)

    if m1 == m2:
        return 1.0

    return SequenceMatcher(None, m1, m2).ratio()


def enrich():
    print("🧠 P1: Enrichment Pipeline — paddle_stats_dump.csv → PostgreSQL")
    print("=" * 60)

    if not CSV_PATH.exists():
        print(f"❌ CSV not found: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH, header=None)
    print(f"📦 CSV loaded: {len(df)} paddles with real specs")

    init_db_sync()

    with Session(sync_engine) as session:
        # Load all paddles + brands
        paddles = session.exec(
            select(PaddleMaster).join(Brand, PaddleMaster.brand_id == Brand.id)
        ).all()

        # Pre-load brands by id
        brands = {b.id: b for b in session.exec(select(Brand)).all()}

        print(f"🎾 DB paddles: {len(paddles)}")

        # Build CSV lookup: {(brand_norm, model_norm): row}
        csv_lookup = {}
        for _, row in df.iterrows():
            b = normalize(str(row[COL_BRAND]))
            m = clean_model(str(row[COL_MODEL]))
            csv_lookup[(b, m)] = row

        enriched = 0
        already_complete = 0
        no_match = 0
        updated_fields_total = {}

        for paddle in paddles:
            brand = brands.get(paddle.brand_id)
            if not brand:
                continue

            brand_norm = normalize(brand.name)
            model_norm = clean_model(paddle.model_name)

            # Try exact match first
            csv_row = csv_lookup.get((brand_norm, model_norm))

            # Try fuzzy match if exact fails
            if csv_row is None:
                best_score = 0.0
                best_row = None
                for (cb, cm), row in csv_lookup.items():
                    if cb != brand_norm:
                        continue
                    s = SequenceMatcher(None, model_norm, cm).ratio()
                    if s > best_score and s >= 0.65:
                        best_score = s
                        best_row = row
                if best_row is not None:
                    csv_row = best_row

            if csv_row is None:
                no_match += 1
                continue

            # Check what's missing and fill
            updates = {}

            sw = clean_int(csv_row[COL_SWING_WEIGHT])
            tw = clean_float(csv_row[COL_TWIST_WEIGHT])
            sr = clean_int(csv_row[COL_SPIN_RPM])
            pw = clean_float(csv_row[COL_POWER])
            cm = clean_float(csv_row[COL_CORE_MM])
            hl = clean_str(csv_row[COL_HANDLE_LENGTH])
            gc = clean_str(csv_row[COL_GRIP_CIRC])
            core_mat = clean_str(csv_row[COL_CORE_MATERIAL])
            shape_str = clean_str(csv_row[COL_SHAPE])
            face_str = clean_str(csv_row[COL_FACE_MATERIAL_2])

            if paddle.swing_weight is None and sw:
                updates['swing_weight'] = sw
            if paddle.twist_weight is None and tw:
                updates['twist_weight'] = tw
            if paddle.spin_rpm is None and sr:
                updates['spin_rpm'] = sr
            if paddle.power_rating is None and pw:
                from app.db.seed_data_hybrid import normalize_rating
                updates['power_rating'] = normalize_rating(pw)
            if paddle.power_original is None and pw:
                updates['power_original'] = pw
            if paddle.core_thickness_mm is None and cm:
                updates['core_thickness_mm'] = cm
            if paddle.handle_length is None and hl:
                updates['handle_length'] = hl
            if paddle.grip_circumference is None and gc:
                updates['grip_circumference'] = gc
            if paddle.core_material is None and core_mat:
                updates['core_material'] = core_mat
            if paddle.shape is None and shape_str:
                s = infer_shape(shape_str)
                if s:
                    updates['shape'] = s
            if paddle.face_material is None and face_str:
                f = infer_face_material(face_str)
                if f:
                    updates['face_material'] = f

            if not updates:
                already_complete += 1
                continue

            # Apply updates
            for field, value in updates.items():
                setattr(paddle, field, value)
                updated_fields_total[field] = updated_fields_total.get(field, 0) + 1

            # Update source tracking
            if 'int_match' not in (paddle.specs_source or ''):
                paddle.specs_source = f"{paddle.specs_source or 'unknown'}+csv_enriched"

            # Recalculate confidence based on data completeness
            real_fields = sum(1 for v in [paddle.swing_weight, paddle.twist_weight, paddle.spin_rpm, paddle.power_rating] if v is not None)
            paddle.specs_confidence = real_fields / 4.0

            enriched += 1

        session.commit()

        print(f"\n{'=' * 60}")
        print(f"✅ ENRICHMENT COMPLETE")
        print(f"   🟢 Enriched:        {enriched}")
        print(f"   ⚪ Already complete: {already_complete}")
        print(f"   🔴 No CSV match:    {no_match}")
        print(f"\n📊 Fields updated:")
        for field, count in sorted(updated_fields_total.items(), key=lambda x: -x[1]):
            print(f"   {field}: {count}")

        # Final stats
        total = len(paddles)
        real = session.exec(select(PaddleMaster).where(
            PaddleMaster.spin_rpm.is_not(None),
            PaddleMaster.twist_weight.is_not(None),
        )).all()
        print(f"\n🎯 DATA QUALITY: {len(real)}/{total} paddles with real performance data ({len(real)/total*100:.0f}%)")


if __name__ == "__main__":
    enrich()
