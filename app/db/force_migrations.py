import sys
import os
from sqlalchemy import create_engine, text

def run_migration():
    db_url = os.getenv("DATABASE_URL_SYNC")
    if not db_url:
        print("DATABASE_URL_SYNC not set.")
        sys.exit(1)
        
    engine = create_engine(db_url)
    
    missing_columns = [
        "core_thickness_mm FLOAT",
        "core_material VARCHAR",
        "face_material VARCHAR",
        "shape VARCHAR",
        "swing_weight INTEGER",
        "twist_weight FLOAT",
        "spin_rpm INTEGER",
        "power_original FLOAT",
        "handle_length VARCHAR",
        "grip_circumference VARCHAR",
        "power_rating INTEGER",
        "control_rating INTEGER",
        "spin_rating INTEGER",
        "sweet_spot_rating INTEGER",
        "available_in_brazil BOOLEAN DEFAULT FALSE",
        "image_url VARCHAR",
        "is_featured BOOLEAN DEFAULT FALSE",
        "specs_source VARCHAR DEFAULT 'manual'",
        "specs_confidence FLOAT DEFAULT 1.0"
    ]
    
    with engine.begin() as conn:
        for col in missing_columns:
            try:
                # PostgreSQL requires IF NOT EXISTS for ADD COLUMN only in newer versions, 
                # but we can try it. If it fails, we handle it.
                conn.execute(text(f"ALTER TABLE paddle_master ADD COLUMN IF NOT EXISTS {col}"))
                print(f"Added column {col}")
            except Exception as e:
                print(f"Skipped {col} (might already exist): {e}")

if __name__ == "__main__":
    run_migration()
