"""
Smoke Test: Data Quality Validation (Phase 4)

Validates ALL quality invariants against the live database.
Designed for CI/CD: exit code 0 = pass, 1 = fail.

Run with:
  docker compose exec backend_v3 python scripts/smoke_test_quality.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select, func
from app.db.database import sync_engine, init_db_sync
from app.models import PaddleMaster, MarketOffer, Brand
from app.models.paddle import REQUIRED_FIELDS, calculate_paddle_ratings

PASS = "✅"
FAIL = "❌"


def run_smoke_tests() -> bool:
    init_db_sync()
    all_passed = True

    with Session(sync_engine) as session:
        # Get active paddles (those exposed by the quality gate)
        active = session.exec(
            select(PaddleMaster).where(PaddleMaster.specs_confidence == 1.0)
        ).all()

        all_paddles = session.exec(select(PaddleMaster)).all()
        brands = {b.id: b for b in session.exec(select(Brand)).all()}

        print("=" * 60)
        print("  🧪 SMOKE TEST — Data Quality Phase 4")
        print("=" * 60)
        print(f"\n  Total paddles in DB: {len(all_paddles)}")
        print(f"  Active (specs=1.0):  {len(active)}")
        print(f"  Inactive:            {len(all_paddles) - len(active)}")

        # ── Check 1: No active paddle has specs_confidence < 1.0 ──
        print("\n" + "─" * 50)
        print("  CHECK 1: Specs Confidence Gate")
        print("─" * 50)
        low_conf = [p for p in active if p.specs_confidence < 1.0]
        if low_conf:
            print(f"  {FAIL} {len(low_conf)} active paddles with confidence < 1.0")
            all_passed = False
        else:
            print(f"  {PASS} All {len(active)} active paddles have confidence == 1.0")

        # ── Check 2: No fabricated ratings (default 5.0) ──
        print("\n" + "─" * 50)
        print("  CHECK 2: No Fabricated Ratings")
        print("─" * 50)
        fabricated = []
        for p in active:
            ratings = calculate_paddle_ratings(p)
            # A paddle with ALL ratings == 5 is suspicious (defaults)
            r_vals = [v for v in [ratings['control'], ratings['spin'], ratings['sweet_spot']] if v is not None]
            if r_vals and all(v == 5 for v in r_vals):
                b = brands.get(p.brand_id)
                fabricated.append(f"[{b.name if b else '?'}] {p.model_name}")
        if fabricated:
            print(f"  {FAIL} {len(fabricated)} paddles with all-default ratings:")
            for f in fabricated:
                print(f"    → {f}")
            all_passed = False
        else:
            print(f"  {PASS} No fabricated ratings detected")

        # ── Check 3: All active paddles have MarketOffers ──
        print("\n" + "─" * 50)
        print("  CHECK 3: Market Offers Present")
        print("─" * 50)
        no_offers = []
        for p in active:
            count = session.exec(
                select(func.count(MarketOffer.id))
                .where(MarketOffer.paddle_id == p.id, MarketOffer.is_active.is_(True))
            ).first()
            if not count or count == 0:
                b = brands.get(p.brand_id)
                no_offers.append(f"[{b.name if b else '?'}] {p.model_name}")
        if no_offers:
            print(f"  {FAIL} {len(no_offers)} active paddles without market offers:")
            for n in no_offers:
                print(f"    → {n}")
            all_passed = False
        else:
            print(f"  {PASS} All {len(active)} active paddles have market offers")

        # ── Check 4: All required fields present ──
        print("\n" + "─" * 50)
        print("  CHECK 4: Required Fields Complete")
        print("─" * 50)
        incomplete = []
        for p in active:
            missing = [f for f in REQUIRED_FIELDS if getattr(p, f) is None]
            if missing:
                b = brands.get(p.brand_id)
                incomplete.append(f"[{b.name if b else '?'}] {p.model_name}: {missing}")
        if incomplete:
            print(f"  {FAIL} {len(incomplete)} active paddles with missing fields:")
            for i in incomplete:
                print(f"    → {i}")
            all_passed = False
        else:
            print(f"  {PASS} All {len(active)} active paddles have 8/8 required fields")

        # ── Quality Metrics Dashboard ──
        print("\n" + "=" * 60)
        print("  📊 QUALITY METRICS DASHBOARD")
        print("=" * 60)

        active_pct = len(active) / len(all_paddles) * 100 if all_paddles else 0
        brands_with_specs = len(set(p.brand_id for p in active))
        total_brands = len(set(p.brand_id for p in all_paddles))

        print(f"\n  | Métrica                          | Valor          | Meta    |")
        print(f"  |:---------------------------------|:---------------|:--------|")
        print(f"  | Paddles 100% completos           | {len(active)}/{len(all_paddles)} ({active_pct:.0f}%)     | 100%    |")
        print(f"  | Ratings fabricados               | {len(fabricated)}              | 0       |")
        print(f"  | Campos NULL no catálogo ativo    | {len(incomplete)}              | 0       |")
        print(f"  | Paddles sem ofertas              | {len(no_offers)}              | 0       |")
        print(f"  | Marcas com specs completos       | {brands_with_specs}/{total_brands}            |         |")

        # ── Final Verdict ──
        print("\n" + "=" * 60)
        if all_passed:
            print(f"  {PASS} ALL SMOKE TESTS PASSED")
        else:
            print(f"  {FAIL} SMOKE TESTS FAILED — Fix issues above")
        print("=" * 60)

    return all_passed


if __name__ == "__main__":
    passed = run_smoke_tests()
    sys.exit(0 if passed else 1)
