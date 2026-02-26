"""
Enrich DB paddles from scraped Brazilian store product page specs.
Reads scraped_product_specs.json and matches against paddle_master by brand + model substring.

Run:
  docker compose exec backend_v3 python scripts/enrich_from_scrape.py
  docker compose exec backend_v3 python scripts/enrich_from_scrape.py --dry-run
"""
import sys
import re
import json
import argparse
from pathlib import Path
from difflib import SequenceMatcher

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from app.db.database import sync_engine, init_db_sync
from app.models import Brand, PaddleMaster

JSON_PATH = Path(__file__).parent.parent / "app" / "data" / "scraped_product_specs.json"


def normalize(text: str) -> str:
    import unicodedata
    text = str(text)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


NOISE = {'raquete', 'de', 'pickleball', 'kit', 'paddle', 'raquetes', 'para'}


def clean_model(text: str) -> str:
    words = normalize(text).split()
    return ' '.join(w for w in words if w not in NOISE)


def fuzzy_match(a: str, b: str) -> float:
    ratio = SequenceMatcher(None, a, b).ratio()
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if shorter and shorter in longer and len(shorter) >= 4:
        ratio = max(ratio, 0.82)
    return ratio


NON_PADDLE_KEYWORDS = {'kit de pickleball', 'mala', 'mochila', 'raqueteira', 'bolsa', 'bola', 'case', 'duffle'}


def is_paddle(model_name: str) -> bool:
    n = normalize(model_name)
    return not any(kw in n for kw in NON_PADDLE_KEYWORDS)


def enrich(dry_run: bool = False):
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"🔍 Enrich from Scraped Specs [{mode}]")
    print("=" * 60)

    if not JSON_PATH.exists():
        print(f"❌ JSON not found: {JSON_PATH}")
        return

    with open(JSON_PATH) as f:
        scraped = json.load(f)

    print(f"📦 Loaded {len(scraped)} scraped spec entries")

    init_db_sync()

    with Session(sync_engine) as session:
        paddles = session.exec(
            select(PaddleMaster).where(PaddleMaster.specs_confidence == 0)
        ).all()
        brands = {b.id: b for b in session.exec(select(Brand)).all()}

        print(f"🎾 {len(paddles)} paddles with specs_confidence=0\n")

        enriched = 0
        skipped_non_paddle = 0
        no_match = 0

        for paddle in paddles:
            brand = brands.get(paddle.brand_id)
            if not brand:
                continue

            if not is_paddle(paddle.model_name):
                skipped_non_paddle += 1
                print(f"  ⏭️  SKIP (non-paddle): {paddle.model_name}")
                continue

            db_brand = normalize(brand.name)
            db_model = clean_model(paddle.model_name)

            # Find best matching scraped entry
            best_score = 0.0
            best_entry = None
            for entry in scraped:
                if normalize(entry['brand']) != db_brand:
                    continue
                entry_model = clean_model(entry['model_pattern'])
                score = fuzzy_match(db_model, entry_model)
                if score > best_score and score >= 0.55:
                    best_score = score
                    best_entry = entry

            if not best_entry:
                no_match += 1
                print(f"  ❌ NO MATCH [{brand.name}] {paddle.model_name}")
                continue

            print(f"  ✅ ({best_score:.2f}) [{brand.name}] {paddle.model_name} → {best_entry['model_pattern']}")

            updates = {}
            if paddle.core_thickness_mm is None and best_entry.get('core_thickness_mm'):
                updates['core_thickness_mm'] = best_entry['core_thickness_mm']
            if paddle.face_material is None and best_entry.get('face_material'):
                updates['face_material'] = best_entry['face_material']
            if paddle.core_material is None and best_entry.get('core_material'):
                updates['core_material'] = best_entry['core_material']
            if paddle.shape is None and best_entry.get('shape'):
                updates['shape'] = best_entry['shape']

            if not updates:
                continue

            enriched += 1

            if not dry_run:
                for field, value in updates.items():
                    setattr(paddle, field, value)
                paddle.specs_source = f"br_scrape_{best_entry['source']}"
                # Confidence: count populated core spec fields
                core_fields = [paddle.swing_weight, paddle.twist_weight, paddle.spin_rpm, paddle.power_rating]
                real = sum(1 for v in core_fields if v is not None)
                # Add partial credit for structural specs
                struct_fields = [paddle.core_thickness_mm, paddle.face_material, paddle.core_material]
                struct = sum(1 for v in struct_fields if v is not None)
                paddle.specs_confidence = min(1.0, (real / 4.0) + (struct * 0.1))

        if not dry_run:
            session.commit()

    print(f"\n{'=' * 60}")
    print(f"✅ ENRICHMENT {'PREVIEW' if dry_run else 'COMPLETE'}")
    print(f"   🟢 Enriched:         {enriched}")
    print(f"   ⏭️  Non-paddles:      {skipped_non_paddle}")
    print(f"   🔴 No match:         {no_match}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    enrich(dry_run=args.dry_run)
