"""
Seed script to populate the database with paddle data from CSV.
Run with: python -m app.db.seed_data
"""
import math
import os
import re
from typing import Optional
from decimal import Decimal
from pathlib import Path

import pandas as pd
from sqlmodel import Session, select, func

from app.db.database import sync_engine, init_db_sync
from app.models import Brand, PaddleMaster, MarketOffer
from app.models.enums import FaceMaterial, PaddleShape

# Path to the CSV file
CSV_PATH = Path("data/raw/paddle_stats_dump.csv")

def extract_brand_name(row_brand: str) -> str:
    """Clean brand name."""
    return str(row_brand).strip()

def infer_face_material(name: str) -> Optional[FaceMaterial]:
    """Try to infer face material from paddle name, else None."""
    name_lower = name.lower()
    if "kevlar" in name_lower or "ruby" in name_lower:
        return FaceMaterial.KEVLAR
    if "fiberglass" in name_lower or "composite" in name_lower:
        return FaceMaterial.FIBERGLASS
    if "hybrid" in name_lower:
        return FaceMaterial.HYBRID
    if "carbon" in name_lower or "graphite" in name_lower:
        return FaceMaterial.CARBON
    
    # User requested NO defaults if missing/unknown
    return None

def infer_shape(name: str) -> Optional[PaddleShape]:
    """Try to infer shape from paddle name, else None."""
    name_lower = name.lower()
    if "elongated" in name_lower or "blade" in name_lower:
        return PaddleShape.ELONGATED
    if "wide" in name_lower or "widebody" in name_lower or "quad" in name_lower:
        return PaddleShape.WIDEBODY
    if "standard" in name_lower or "classic" in name_lower:
        return PaddleShape.STANDARD
        
    # User requested NO defaults if missing/unknown
    return None

def normalize_rating(value) -> Optional[int]:
    """Normalize a value to an integer rating 0-10. Return None if missing."""
    if pd.isna(value) or value == 0 or str(value).strip() in ["", "0", "nan"]:
        return None
    
    try:
        val_float = float(value)
        if val_float <= 10.0:
            return min(10, max(0, round(val_float)))
        
        # Heuristic for RPM ~200-250 -> 5-10 range
        if val_float > 100:
             score = (val_float - 150) / 10
             return min(10, max(0, round(score)))
             
        return min(10, max(0, round(val_float)))
    except (ValueError, TypeError):
        return None

def clean_price(price_val) -> Optional[Decimal]:
    """Clean price to Decimal, or None."""
    if pd.isna(price_val):
        return None
    try:
        if isinstance(price_val, str):
             # Remove currency symbols 
             clean = re.sub(r'[^\d.]', '', price_val)
             if not clean: return None
             return Decimal(clean)
        return Decimal(str(price_val))
    except:
        return None

def clean_thickness(val) -> Optional[float]:
    """Clean core thickness, or None."""
    if pd.isna(val) or val == 0:
        return None
    try:
        return float(val)
    except:
        return None

def clean_float(val) -> Optional[float]:
    """Clean generic float value."""
    if pd.isna(val) or str(val).strip() in ["", "nan"]:
        return None
    try:
        return float(val)
    except:
        return None

def clean_int(val) -> Optional[int]:
    """Clean generic int value."""
    if pd.isna(val) or str(val).strip() in ["", "nan"]:
        return None
    try:
        return int(float(val))
    except:
        return None

def clean_str(val) -> Optional[str]:
    """Clean string value."""
    if pd.isna(val) or str(val).strip() in ["", "nan"]:
        return None
    return str(val).strip()

def seed_database():
    """Main function to seed the database from CSV."""
    if not CSV_PATH.exists():
        print(f"❌ Error: CSV file not found at {CSV_PATH}")
        return

    # Ensure tables exist
    init_db_sync()
    
    # Read CSV
    print(f"📖 Reading CSV from {CSV_PATH}...")
    try:
        df = pd.read_csv(CSV_PATH)
        print(f"📊 Found {len(df)} rows.")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    with Session(sync_engine) as session:
        brands_cache = {}
        paddles_updated = 0
        paddles_created = 0
        
        print(f"Columns: {df.columns.tolist()}")
        for index, row in df.iterrows():
            if index == 0: print(f"Sample Row: {row}")
            # 1. Handle Brand
            raw_brand = row.get("Col_0")
            if pd.isna(raw_brand) or str(raw_brand).strip() in ["0", "nan", ""]:
                continue

            brand_name = extract_brand_name(raw_brand)
            if not brand_name:
                continue
                
            if brand_name not in brands_cache:
                # Check DB first
                brand = session.exec(select(Brand).where(Brand.name == brand_name)).first()
                if not brand:
                    brand = Brand(name=brand_name, website="")
                    session.add(brand)
                    session.flush() # Get ID
                brands_cache[brand_name] = brand
            
            brand_obj = brands_cache[brand_name]

            # 2. Extract Paddle Data
            raw_model = row.get("Col_1")
            if pd.isna(raw_model) or str(raw_model).strip() in ["0", "nan", ""]:
                continue
                
            model_name = str(raw_model)
            price = clean_price(row.get("Col_2"))
            
            # Ratings & Specs
            power_rating = normalize_rating(row.get("Col_6"))
            spin_rating = normalize_rating(row.get("Col_5"))
            
            # Missing in CSV -> None
            control_rating = None
            sweet_spot_rating = None
            
            core_mm = clean_thickness(row.get("Col_7"))
            
            # Infer Stats -> None if inference fails
            # Try to grab detailed materials from new columns
            core_material_raw = clean_str(row.get("Col_14")) # Core
            face_material_raw = clean_str(row.get("Col_13")) # Face
            
            face_material = infer_face_material(str(face_material_raw)) if face_material_raw else infer_face_material(model_name)
            if not face_material:
                # Try fallback face column
                face_material_raw_2 = clean_str(row.get("Col_12"))
                if face_material_raw_2:
                    face_material = infer_face_material(str(face_material_raw_2))
            
            shape = infer_shape(clean_str(row.get("Col_11")) or model_name)
            
            # New Stats
            swing_weight = clean_int(row.get("Col_3"))
            twist_weight = clean_float(row.get("Col_4"))
            spin_rpm = clean_int(row.get("Col_5"))
            power_original = clean_float(row.get("Col_6"))
            handle_length = clean_str(row.get("Col_8"))
            grip_circumference = clean_str(row.get("Col_9")) 

            # 3. Create or Update Paddle
            keywords = [brand_name.lower(), model_name.lower()]
            if core_mm: keywords.append(f"{int(core_mm)}mm")
            
            # Check if paddle exists
            # print(f"Querying DB for {brand_name} {model_name}...")
            paddle = session.exec(select(PaddleMaster).where(
                PaddleMaster.brand_id == brand_obj.id,
                PaddleMaster.model_name == model_name
            )).first()

            if paddle:
                # Update existing
                paddle.search_keywords = keywords
                paddle.core_thickness_mm = core_mm
                paddle.face_material = face_material
                paddle.core_material = core_material_raw
                paddle.shape = shape
                paddle.power_rating = power_rating
                paddle.swing_weight = swing_weight
                paddle.twist_weight = twist_weight
                paddle.spin_rpm = spin_rpm
                paddle.power_original = power_original
                paddle.handle_length = handle_length
                paddle.grip_circumference = grip_circumference
                paddle.specs_source = "csv_dump_verified"
                session.add(paddle)
                paddles_updated += 1
            else:
                # Create new
                paddle = PaddleMaster(
                    brand_id=brand_obj.id,
                    model_name=model_name,
                    search_keywords=keywords,
                    core_thickness_mm=core_mm,
                    face_material=face_material,
                    core_material=core_material_raw,
                    shape=shape,
                    power_rating=power_rating, 
                    is_featured=False,
                    specs_source="csv_dump_verified",
                    swing_weight=swing_weight,
                    twist_weight=twist_weight,
                    spin_rpm=spin_rpm,
                    power_original=power_original,
                    handle_length=handle_length,
                    grip_circumference=grip_circumference,
                )
                session.add(paddle)
                paddles_created += 1
            
            session.flush()

            # 4. Create Market Offer (Upsert logic for simple MSRP offer)
            if price:
                price_brl = price * Decimal("5.5")
                # Check for existing MSRP offer
                offer = session.exec(select(MarketOffer).where(
                    MarketOffer.paddle_id == paddle.id,
                    MarketOffer.store_name == "MSRP (Import)"
                )).first()
                
                if offer:
                    offer.price_brl = price_brl
                    session.add(offer)
                else:
                    offer = MarketOffer(
                        paddle_id=paddle.id,
                        store_name="MSRP (Import)",
                        price_brl=price_brl,
                        url=f"https://example.com/search?q={brand_name}+{model_name.replace(' ', '+')}"
                    )
                    session.add(offer)

        session.commit()
        print(f"✅ Processed {len(df)} rows.")
        print(f"✅ Created {paddles_created} new paddles.")
        print(f"✅ Updated {paddles_updated} existing paddles.")
        print("🎉 Database sync completed!")

if __name__ == "__main__":
    seed_database()
