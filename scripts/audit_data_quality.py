"""
Data Quality Audit — Phase 1: Pipeline Invertido + Auditoria

Maps field coverage, cross-references BR catalog with US dump,
detects non-paddles/duplicates, and recalculates specs_confidence.

Run with:
  docker compose exec backend_v3 python scripts/audit_data_quality.py
  docker compose exec backend_v3 python scripts/audit_data_quality.py --fix
"""
import sys
import re
import argparse
from collections import defaultdict
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd
from sqlmodel import Session, select, func

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import sync_engine, init_db_sync
from app.models import Brand, PaddleMaster, MarketOffer
from app.models.paddle import calculate_specs_confidence, calculate_control

CSV_PATH = Path(__file__).parent.parent / "app" / "data" / "paddle_stats_dump.csv"

REQUIRED_FIELDS = [
    'core_thickness_mm', 'face_material', 'core_material', 'shape',
    'swing_weight', 'spin_rpm', 'power_rating', 'handle_length',
]

NON_PADDLE_KEYWORDS = [
    'mala', 'mochila', 'bolsa', 'capa', 'rede', 'kit', 'bola', 'ball',
    'tshirt', 'camiseta', 'raqueteira', 'tênis', 'tenis', 'short', 'meia',
    'grip', 'overgrip', 'lead tape', 'caneleira', 'munhequeira', 'bag',
    'backpack', 'cover', 'net', 'shoe', 'socks',
]


def normalize(text: str) -> str:
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


def fuzzy_score(m1: str, m2: str) -> float:
    ratio = SequenceMatcher(None, m1, m2).ratio()
    shorter, longer = (m1, m2) if len(m1) <= len(m2) else (m2, m1)
    if shorter and shorter in longer and len(shorter) >= 4:
        ratio = max(ratio, 0.80)
    return ratio


def is_non_paddle(model_name: str) -> bool:
    lower = model_name.lower()
    return any(kw in lower for kw in NON_PADDLE_KEYWORDS)


def audit(fix: bool = False):
    mode = "FIX MODE" if fix else "AUDIT ONLY"
    print(f"\n{'='*70}")
    print(f"  📊 DATA QUALITY AUDIT — Phase 1 [{mode}]")
    print(f"{'='*70}\n")

    init_db_sync()

    # Load US dump
    if not CSV_PATH.exists():
        print(f"❌ US CSV dump not found: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH, header=None, on_bad_lines='skip')
    print(f"📦 US Dump: {len(df)} paddles loaded\n")

    csv_lookup: dict[tuple[str, str], any] = {}
    for _, row in df.iterrows():
        b = normalize(str(row[0]))
        m = normalize(str(row[1]))
        if b and m:
            csv_lookup[(b, m)] = row

    with Session(sync_engine) as session:
        paddles = session.exec(
            select(PaddleMaster).join(Brand, PaddleMaster.brand_id == Brand.id)
        ).all()
        brands = {b.id: b for b in session.exec(select(Brand)).all()}

        total = len(paddles)
        print(f"🎾 DB Catalog: {total} paddles\n")

        # ═══════════════════════════════════════════════════════════════════
        # 1. FIELD COVERAGE
        # ═══════════════════════════════════════════════════════════════════
        print(f"{'─'*50}")
        print("  📐 1. FIELD COVERAGE (8 Required Fields)")
        print(f"{'─'*50}")

        field_filled = defaultdict(int)
        field_null = defaultdict(int)
        complete_count = 0
        incomplete_paddles = []

        for paddle in paddles:
            all_filled = True
            for field in REQUIRED_FIELDS:
                val = getattr(paddle, field, None)
                if val is not None:
                    field_filled[field] += 1
                else:
                    field_null[field] += 1
                    all_filled = False

            if all_filled:
                complete_count += 1
            else:
                brand = brands.get(paddle.brand_id)
                missing = [f for f in REQUIRED_FIELDS if getattr(paddle, f) is None]
                incomplete_paddles.append({
                    'brand': brand.name if brand else '?',
                    'model': paddle.model_name,
                    'missing': missing,
                })

        for field in REQUIRED_FIELDS:
            filled = field_filled[field]
            pct = filled / total * 100 if total else 0
            bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
            status = "✅" if pct == 100 else "⚠️" if pct >= 50 else "🔴"
            print(f"  {status} {field:25s} {bar} {filled:3d}/{total} ({pct:.0f}%)")

        print(f"\n  📊 Complete specs (all 8 fields): {complete_count}/{total} ({complete_count/total*100:.0f}%)")
        print(f"  📊 Incomplete:                    {len(incomplete_paddles)}/{total}")

        # ═══════════════════════════════════════════════════════════════════
        # 2. US DUMP MATCH
        # ═══════════════════════════════════════════════════════════════════
        print(f"\n{'─'*50}")
        print("  🔗 2. BR → US DUMP MATCH")
        print(f"{'─'*50}")

        matched = []
        unmatched = []
        near_misses = []

        for paddle in paddles:
            brand = brands.get(paddle.brand_id)
            if not brand:
                unmatched.append(('?', paddle.model_name, 0.0))
                continue

            brand_norm = normalize(brand.name)
            model_norm = normalize(paddle.model_name)

            # Exact match
            if (brand_norm, model_norm) in csv_lookup:
                matched.append((brand.name, paddle.model_name, 1.0))
                continue

            # Fuzzy match
            best_score = 0.0
            for (cb, cm) in csv_lookup:
                if cb != brand_norm:
                    continue
                s = fuzzy_score(model_norm, cm)
                if s > best_score:
                    best_score = s

            if best_score >= 0.60:
                matched.append((brand.name, paddle.model_name, best_score))
            elif best_score >= 0.50:
                near_misses.append((brand.name, paddle.model_name, best_score))
            else:
                unmatched.append((brand.name, paddle.model_name, best_score))

        print(f"  ✅ Matched:      {len(matched):3d}/{total}")
        print(f"  🟡 Near miss:    {len(near_misses):3d}/{total}  (0.50-0.59)")
        print(f"  ❌ No match:     {len(unmatched):3d}/{total}")

        if near_misses:
            print(f"\n  🟡 Near Misses (consider lowering threshold):")
            for brand, model, score in sorted(near_misses, key=lambda x: -x[2]):
                print(f"     [{brand}] {model} (score: {score:.2f})")

        if unmatched:
            print(f"\n  ❌ No Match (candidates for removal):")
            for brand, model, score in sorted(unmatched, key=lambda x: x[0]):
                print(f"     [{brand}] {model}")

        # ═══════════════════════════════════════════════════════════════════
        # 2.5. VALIDATION SOURCES DISTRIBUTION
        # ═══════════════════════════════════════════════════════════════════
        print(f"\n{'─'*50}")
        print("  ✅ 2.5. VALIDATION SOURCES")
        print(f"{'─'*50}")

        sources_counts = defaultdict(int)
        for paddle in paddles:
            sources = getattr(paddle, 'validation_sources', []) or []
            if not sources:
                sources_counts["none"] += 1
            for source in sources:
                sources_counts[source] += 1
                
        for source, count in sorted(sources_counts.items(), key=lambda x: -x[1]):
            print(f"  {source:15s}: {count:3d} paddles")

        # ═══════════════════════════════════════════════════════════════════
        # 3. NON-PADDLE DETECTION
        # ═══════════════════════════════════════════════════════════════════
        print(f"\n{'─'*50}")
        print("  🧹 3. NON-PADDLE DETECTION")
        print(f"{'─'*50}")

        non_paddles = []
        for paddle in paddles:
            if is_non_paddle(paddle.model_name):
                brand = brands.get(paddle.brand_id)
                non_paddles.append((brand.name if brand else '?', paddle.model_name, paddle.id))

        if non_paddles:
            print(f"  🔴 Found {len(non_paddles)} non-paddles:")
            for brand, model, pid in non_paddles:
                print(f"     [{brand}] {model}")
        else:
            print(f"  ✅ No non-paddles detected")

        # ═══════════════════════════════════════════════════════════════════
        # 4. DUPLICATE DETECTION
        # ═══════════════════════════════════════════════════════════════════
        print(f"\n{'─'*50}")
        print("  🔍 4. DUPLICATE DETECTION (cross-store)")
        print(f"{'─'*50}")

        seen: dict[str, list] = defaultdict(list)
        for paddle in paddles:
            brand = brands.get(paddle.brand_id)
            key = f"{normalize(brand.name if brand else '')}|{normalize(paddle.model_name)}"
            seen[key].append(paddle)

        dupes = {k: v for k, v in seen.items() if len(v) > 1}
        if dupes:
            print(f"  ⚠️ Found {len(dupes)} duplicate groups:")
            for key, group in dupes.items():
                brand, model = key.split('|', 1)
                print(f"     [{brand}] {model} × {len(group)} entries")
        else:
            print(f"  ✅ No duplicates detected")

        # ═══════════════════════════════════════════════════════════════════
        # 5. MARKET OFFER CHECK
        # ═══════════════════════════════════════════════════════════════════
        print(f"\n{'─'*50}")
        print("  💰 5. MARKET OFFER CHECK")
        print(f"{'─'*50}")

        offer_counts = dict(
            session.exec(
                select(MarketOffer.paddle_id, func.count(MarketOffer.id))
                .where(MarketOffer.is_active == True)  # noqa: E712
                .group_by(MarketOffer.paddle_id)
            ).all()
        )

        with_offers = sum(1 for p in paddles if p.id in offer_counts)
        without_offers = total - with_offers

        print(f"  ✅ With active offers:    {with_offers}")
        print(f"  🔴 Without active offers: {without_offers}")

        low_price = []
        for paddle in paddles:
            if paddle.id in offer_counts:
                min_price = session.exec(
                    select(func.min(MarketOffer.price_brl))
                    .where(MarketOffer.paddle_id == paddle.id, MarketOffer.is_active == True)  # noqa: E712
                ).one()
                if min_price and float(min_price) < 450:
                    brand = brands.get(paddle.brand_id)
                    low_price.append((brand.name if brand else '?', paddle.model_name, float(min_price)))

        if low_price:
            print(f"\n  ⚠️ Leisure paddles (< R$ 450):")
            for brand, model, price in sorted(low_price, key=lambda x: x[2]):
                print(f"     [{brand}] {model} — R$ {price:.0f}")

        # ═══════════════════════════════════════════════════════════════════
        # 6. FIX MODE — Recalculate specs_confidence
        # ═══════════════════════════════════════════════════════════════════
        if fix:
            print(f"\n{'─'*50}")
            print("  🔧 6. APPLYING FIXES")
            print(f"{'─'*50}")

            updated = 0
            for paddle in paddles:
                old_conf = paddle.specs_confidence
                new_conf = calculate_specs_confidence(paddle)

                if old_conf != new_conf:
                    paddle.specs_confidence = new_conf
                    updated += 1
                    brand = brands.get(paddle.brand_id)
                    print(f"  📝 [{brand.name if brand else '?'}] {paddle.model_name}: "
                          f"specs_confidence {old_conf:.1f} → {new_conf:.1f}")

            session.commit()
            print(f"\n  ✅ Updated specs_confidence for {updated} paddles")

        # ═══════════════════════════════════════════════════════════════════
        # SUMMARY
        # ═══════════════════════════════════════════════════════════════════
        print(f"\n{'='*70}")
        print(f"  📊 AUDIT SUMMARY")
        print(f"{'='*70}")
        print(f"  Total paddles:           {total}")
        print(f"  Complete specs (100%):   {complete_count} ({complete_count/total*100:.0f}%)")
        print(f"  US dump matches:         {len(matched)} ({len(matched)/total*100:.0f}%)")
        print(f"  Non-paddles detected:    {len(non_paddles)}")
        print(f"  Duplicates:              {len(dupes)} groups")
        print(f"  With market offers:      {with_offers}")
        print(f"  Low-price (< R$ 450):    {len(low_price)}")
        print(f"\n  🎯 Catalog after quality gate (specs=100% + offer):")

        ready = sum(
            1 for p in paddles
            if calculate_specs_confidence(p) == 1.0 and p.id in offer_counts
        )
        ready_hybrid = sum(
            1 for p in paddles
            if calculate_specs_confidence(p) == 1.0 and p.id in offer_counts and len(getattr(p, 'validation_sources', []) or []) >= 1
        )
        print(f"     {ready} paddles ready for production (Total)")
        print(f"     {ready_hybrid} paddles ready for production (Hybrid Pipeline Coverage)")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Quality Audit — Phase 1")
    parser.add_argument("--fix", action="store_true",
                        help="Apply fixes (recalculate specs_confidence)")
    args = parser.parse_args()
    audit(fix=args.fix)
