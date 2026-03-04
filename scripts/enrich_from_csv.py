"""
Enrich existing paddles with real specs from paddle_stats_dump.csv.
Updates ONLY NULL fields — never overwrites manually entered data.

Run with:
  docker compose exec backend_v3 python scripts/enrich_from_csv.py
  docker compose exec backend_v3 python scripts/enrich_from_csv.py --dry-run
"""
import sys
import re
import argparse
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

# CSV Column mapping (verified against actual data, 21 columns total)
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
# col10 = another spin RPM measurement (ignore)
COL_SHAPE = 11          # 'Wide body', 'Elongated', etc.
COL_FACE_MATERIAL_A = 12  # Primary face material text
COL_FACE_MATERIAL_B = 13  # Secondary face material text
COL_CORE_MATERIAL = 13


# ─── Text Cleaning ────────────────────────────────────────────────────────────

# Portuguese / generic noise present in Brazilian store product titles
NOISE_TOKENS = {
    # Portuguese
    'raquete', 'de', 'pickleball', 'kit', 'paddle', 'raquetes',
    # English noise in thickness annotations
    'mm', '14mm', '16mm', '13mm', '12mm', '19mm', '15mm',
    # Generic
    'pro', 'series',
}

# Brand alias map: DB brand name → CSV brand name (lowercase)
BRAND_ALIASES: dict[str, str] = {
    '3rdshot': '3rdshot',
    '3rd shot': '3rdshot',
    'slk': 'slk',
    'selkirk slk': 'slk',
    'proxr': 'proxr',
    'pro-xr': 'proxr',
    'start': 'start',
}


def normalize(text: str) -> str:
    """Lowercase, strip accents, remove non-alphanumeric except spaces."""
    if not text or pd.isna(text):
        return ""
    import unicodedata
    text = str(text)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clean_model(text: str) -> str:
    """Remove noise tokens from a model name."""
    words = normalize(text).split()
    return ' '.join(w for w in words if w not in NOISE_TOKENS)


def resolve_brand(db_brand: str) -> str:
    """Normalize and resolve brand aliases."""
    nb = normalize(db_brand)
    return BRAND_ALIASES.get(nb, nb)


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


def normalize_rating(raw: float) -> int:
    """Normalize a raw power score (typically 6-9) to a 0-10 int scale."""
    if raw is None:
        return None
    clamped = max(0.0, min(10.0, float(raw)))
    return int(round(clamped))


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


def fuzzy_score(m1: str, m2: str) -> float:
    """SequenceMatcher ratio, with a bonus for sub-string containment."""
    ratio = SequenceMatcher(None, m1, m2).ratio()
    # Boost if one is a significant substring of the other
    shorter, longer = (m1, m2) if len(m1) <= len(m2) else (m2, m1)
    if shorter and shorter in longer and len(shorter) >= 4:
        ratio = max(ratio, 0.80)
    return ratio


# ─── Main ────────────────────────────────────────────────────────────────────

def enrich(dry_run: bool = False):
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"🧠 Enrich Pipeline — paddle_stats_dump.csv → PostgreSQL [{mode}]")
    print("=" * 60)

    if not CSV_PATH.exists():
        print(f"❌ CSV not found: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH, header=None, on_bad_lines='skip')
    print(f"📦 CSV: {len(df)} rows loaded")

    init_db_sync()

    with Session(sync_engine) as session:
        paddles = session.exec(
            select(PaddleMaster).join(Brand, PaddleMaster.brand_id == Brand.id)
        ).all()
        brands = {b.id: b for b in session.exec(select(Brand)).all()}

        print(f"🎾 DB: {len(paddles)} paddles\n")

        # Build CSV lookup: {(brand_norm, model_norm): row}
        csv_lookup: dict[tuple[str, str], any] = {}
        for _, row in df.iterrows():
            b = normalize(str(row[COL_BRAND]))
            m = clean_model(str(row[COL_MODEL]))
            if b and m:
                csv_lookup[(b, m)] = row

        enriched = 0
        no_match = 0
        updated_fields_total: dict[str, int] = {}
        match_log = []

        for paddle in paddles:
            brand = brands.get(paddle.brand_id)
            if not brand:
                continue

            brand_norm = resolve_brand(brand.name)
            model_norm = clean_model(paddle.model_name)

            # 1. Exact match
            csv_row = csv_lookup.get((brand_norm, model_norm))
            match_type = "exact"

            # 2. Fuzzy match within same brand
            if csv_row is None:
                best_score = 0.0
                best_row = None
                for (cb, cm), row in csv_lookup.items():
                    if cb != brand_norm:
                        continue
                    s = fuzzy_score(model_norm, cm)
                    if s > best_score and s >= 0.60:
                        best_score = s
                        best_row = row
                if best_row is not None:
                    csv_row = best_row
                    match_type = f"fuzzy({best_score:.2f})"

            if csv_row is None:
                no_match += 1
                match_log.append(f"  ❌ NO MATCH  [{brand.name}] {paddle.model_name!r}")
                continue

            csv_model_display = f"{csv_row[COL_BRAND]} {csv_row[COL_MODEL]}"
            match_log.append(f"  ✅ {match_type:15s} [{brand.name}] {paddle.model_name!r}  →  {csv_model_display!r}")

            # Build updates for NULL fields only
            updates: dict = {}

            sw = clean_int(csv_row[COL_SWING_WEIGHT])
            tw = clean_float(csv_row[COL_TWIST_WEIGHT])
            sr = clean_int(csv_row[COL_SPIN_RPM])
            pw = clean_float(csv_row[COL_POWER])
            cm = clean_float(csv_row[COL_CORE_MM])
            hl = clean_str(csv_row[COL_HANDLE_LENGTH])
            gc = clean_str(csv_row[COL_GRIP_CIRC])
            core_mat = clean_str(csv_row[COL_CORE_MATERIAL])
            shape_str = clean_str(csv_row[COL_SHAPE])
            # Use first non-null face material text
            face_str = clean_str(csv_row[COL_FACE_MATERIAL_A]) or clean_str(csv_row[COL_FACE_MATERIAL_B])

            if paddle.swing_weight is None and sw:
                updates['swing_weight'] = sw
            if paddle.twist_weight is None and tw:
                updates['twist_weight'] = tw
            if paddle.spin_rpm is None and sr:
                updates['spin_rpm'] = sr
            if paddle.power_rating is None and pw:
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
                continue

            enriched += 1
            for field, value in updates.items():
                updated_fields_total[field] = updated_fields_total.get(field, 0) + 1

            if not dry_run:
                for field, value in updates.items():
                    setattr(paddle, field, value)

                paddle.specs_source = f"csv_enriched+{match_type}"
                # Use the new binary specs_confidence from roadmap
                from app.models.paddle import calculate_specs_confidence
                paddle.specs_confidence = calculate_specs_confidence(paddle)

        if not dry_run:
            session.commit()

    # ─── Report ───────────────────────────────────────────────────────────────
    print("\n".join(match_log))
    print(f"\n{'=' * 60}")
    print(f"✅ ENRICHMENT {'PREVIEW' if dry_run else 'COMPLETE'}")
    print(f"   🟢 Enriched:     {enriched}")
    print(f"   🔴 No match:     {no_match}")
    print(f"\n📊 Fields to update:")
    for field, count in sorted(updated_fields_total.items(), key=lambda x: -x[1]):
        print(f"   {field}: {count}")

    total = len(paddles)
    coverage = enriched / total * 100 if total else 0
    print(f"\n🎯 Expected coverage: {enriched}/{total} paddles ({coverage:.0f}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to DB")
    args = parser.parse_args()
    enrich(dry_run=args.dry_run)
