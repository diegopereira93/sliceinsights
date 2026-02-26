"""
Spec Enrichment from Manufacturer Shopify APIs.
Fills NULL fields (core_thickness, face_material, shape, handle_length, image_url)
by querying international manufacturer sites.

Run: docker compose exec -e PYTHONPATH=/app backend_v3 python scripts/enrich_specs_from_manufacturers.py
"""
import re
import time
import html as html_lib
from typing import Optional

import requests
from sqlmodel import Session, select

from app.db.database import sync_engine, init_db_sync
from app.models import PaddleMaster, Brand
from app.models.enums import FaceMaterial, PaddleShape


# --- Utilities ---

def normalize(text: str) -> str:
    if not text:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return re.sub(r"\s+", " ", text)


def infer_face_material(text: str) -> Optional[FaceMaterial]:
    n = (text or "").lower()
    if "kevlar" in n:
        return FaceMaterial.KEVLAR
    if "fiberglass" in n or "composite" in n:
        return FaceMaterial.FIBERGLASS
    if "hybrid" in n:
        return FaceMaterial.HYBRID
    if "carbon" in n or "graphite" in n:
        return FaceMaterial.CARBON
    return None


def infer_shape(text: str) -> Optional[PaddleShape]:
    n = (text or "").lower()
    if "elongated" in n or "blade" in n or "enlongated" in n:
        return PaddleShape.ELONGATED
    if "wide" in n or "widebody" in n:
        return PaddleShape.WIDEBODY
    if "standard" in n or "classic" in n:
        return PaddleShape.STANDARD
    return None


def calc_confidence(paddle) -> float:
    filled = sum(
        1
        for v in [
            paddle.swing_weight,
            paddle.twist_weight,
            paddle.spin_rpm,
            paddle.power_original,
        ]
        if v is not None
    )
    return filled / 4.0


# --- Manufacturer Shopify endpoints ---

MANUFACTURER_SHOPIFY = {
    "selkirk": "selkirk.com",
    "joola": "joola.com",
    "hyperlight": "hyperlight.gg",
    "drop shot": "dropshotequipment.com",
    "vatic": "vaticrocs.com",
    "slk": "selkirk.com",
}

# --- Spec extraction ---

SPEC_PATTERNS = {
    "core_thickness_mm": [
        r"(\d+(?:\.\d+)?)\s*mm\s*(?:core|thickness)",
        r"core[:\s]+(\d+(?:\.\d+)?)\s*mm",
    ],
    "handle_length": [
        r'handle[:\s]+(\d+(?:\.\d+)?)\s*(?:inches?|")',
        r"grip\s*length[:\s]+(\d+(?:\.\d+)?)",
    ],
}


def extract_specs_from_body_html(body_html: str) -> dict:
    text = html_lib.unescape(re.sub(r"<[^>]+>", " ", body_html or "")).lower()
    specs = {}
    for field, patterns in SPEC_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                specs[field] = m.group(1).strip()
                break
    for fm in ["carbon", "fiberglass", "hybrid", "kevlar"]:
        if fm in text:
            specs.setdefault("face_material_text", fm)
            break
    for sh in ["elongated", "widebody", "standard"]:
        if sh in text:
            specs.setdefault("shape_text", sh)
            break
    return specs


def enrich_paddle_in_place(session, paddle, specs: dict, image_url: str = None) -> bool:
    changed = False
    if paddle.image_url is None and image_url:
        paddle.image_url = image_url
        changed = True
    if paddle.core_thickness_mm is None and specs.get("core_thickness_mm"):
        try:
            paddle.core_thickness_mm = float(specs["core_thickness_mm"])
            changed = True
        except (ValueError, TypeError):
            pass
    if paddle.face_material is None and specs.get("face_material_text"):
        fm = infer_face_material(specs["face_material_text"])
        if fm:
            paddle.face_material = fm
            changed = True
    if paddle.shape is None and specs.get("shape_text"):
        sh = infer_shape(specs["shape_text"])
        if sh:
            paddle.shape = sh
            changed = True
    if paddle.handle_length is None and specs.get("handle_length"):
        paddle.handle_length = str(specs["handle_length"])
        changed = True
    if changed:
        paddle.specs_source = (paddle.specs_source or "") + "+manufacturer"
        paddle.specs_confidence = calc_confidence(paddle)
        session.add(paddle)
    return changed


# --- Main enrichment flow ---

def fetch_manufacturer_products(domain: str) -> list[dict]:
    all_products = []
    page = 1
    while True:
        try:
            r = requests.get(
                f"https://{domain}/products.json",
                params={"limit": 250, "page": page},
                timeout=15,
                headers={"User-Agent": "SliceInsights Catalog Bot 1.0"},
            )
            if r.status_code != 200:
                break
            products = r.json().get("products", [])
            if not products:
                break
            all_products.extend(products)
            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️  Error fetching {domain}: {e}")
            break
    return all_products


def main():
    print("🔬 Enriching paddle specs from manufacturer sites...")
    init_db_sync()

    with Session(sync_engine) as session:
        paddles = session.exec(select(PaddleMaster)).all()
        brands = {b.id: b for b in session.exec(select(Brand)).all()}

        # Group paddles by brand for efficient lookups
        brand_paddles: dict[str, list] = {}
        for p in paddles:
            brand = brands.get(p.brand_id)
            if brand:
                key = normalize(brand.name)
                brand_paddles.setdefault(key, []).append(p)

        enriched_total = 0
        for brand_key, domain in MANUFACTURER_SHOPIFY.items():
            matched_paddles = brand_paddles.get(brand_key, [])
            if not matched_paddles:
                print(f"  ⏩ {brand_key}: no paddles in DB, skipping")
                continue

            print(f"\n🌐 Fetching {domain}...")
            mfr_products = fetch_manufacturer_products(domain)
            print(f"  📦 {len(mfr_products)} products from {domain}")

            # Build lookup: normalized title → (body_html, image)
            mfr_lookup = {}
            for mp in mfr_products:
                norm = normalize(mp.get("title", ""))
                image = mp["images"][0]["src"] if mp.get("images") else None
                mfr_lookup[norm] = {
                    "body_html": mp.get("body_html", ""),
                    "image_url": image,
                }

            for paddle in matched_paddles:
                model_norm = normalize(paddle.model_name)
                # Try fuzzy match: find product containing model name
                match = None
                for mfr_title, data in mfr_lookup.items():
                    if model_norm in mfr_title or mfr_title in model_norm:
                        match = data
                        break

                if match:
                    specs = extract_specs_from_body_html(match["body_html"])
                    if enrich_paddle_in_place(session, paddle, specs, match.get("image_url")):
                        enriched_total += 1
                        print(f"  ✅ Enriched: {paddle.model_name}")

        session.commit()
        print(f"\n🏁 Enrichment complete: {enriched_total} paddles updated")

        # Audit confidence
        from sqlmodel import func

        high_conf = session.exec(
            select(func.count(PaddleMaster.id)).where(PaddleMaster.specs_confidence >= 0.5)
        ).one()
        total = session.exec(select(func.count(PaddleMaster.id))).one()
        pct = (high_conf / total * 100) if total else 0
        print(f"📊 Specs confidence ≥ 0.5: {high_conf}/{total} ({pct:.0f}%)")


if __name__ == "__main__":
    main()
