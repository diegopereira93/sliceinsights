import sys
from pathlib import Path
from sqlmodel import Session, select, func
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import sync_engine, init_db_sync
from app.models import PaddleMaster

init_db_sync()

with Session(sync_engine) as session:
    paddles = session.exec(select(PaddleMaster)).all()
    total = len(paddles)
    print(f"Total: {total}")
    
    fields = [
        'core_thickness_mm', 'core_material', 'face_material', 'shape',
        'swing_weight', 'twist_weight', 'spin_rpm', 'power_original',
        'power_rating', 'handle_length', 'grip_circumference', 'image_url',
        'control_rating', 'spin_rating', 'sweet_spot_rating'
    ]
    
    counts = {f: 0 for f in fields}
    for p in paddles:
        for f in fields:
            if getattr(p, f, None) is not None:
                counts[f] += 1
                
    for f in fields:
        print(f"{f}: {counts[f]}")
