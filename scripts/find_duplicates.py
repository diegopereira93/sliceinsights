
import asyncio
from sqlmodel import select, func, Session
from app.db.database import sync_engine
from app.models import PaddleMaster, Brand

def find_duplicates():
    print("--- DUPLICATE CHECK ---")
    with Session(sync_engine) as session:
        # Group by model_name and brand_id
        query = select(
            PaddleMaster.model_name, 
            PaddleMaster.brand_id, 
            func.count(PaddleMaster.id).label("count")
        ).group_by(
            PaddleMaster.model_name, 
            PaddleMaster.brand_id
        ).having(
            func.count(PaddleMaster.id) > 1
        )
        
        duplicates = session.exec(query).all()
        
        if not duplicates:
            print("No duplicates found by name and brand.")
            return

        print(f"Found {len(duplicates)} sets of duplicates:")
        for model_name, brand_id, count in duplicates:
            brand = session.get(Brand, brand_id)
            brand_name = brand.name if brand else f"ID:{brand_id}"
            print(f"- {model_name} ({brand_name}): {count} entries")
            
            # Show the IDs
            item_query = select(PaddleMaster).where(
                PaddleMaster.model_name == model_name,
                PaddleMaster.brand_id == brand_id
            )
            items = session.exec(item_query).all()
            for item in items:
                print(f"  * ID: {item.id}, Specs: SW:{item.swing_weight}, TW:{item.twist_weight}")

if __name__ == "__main__":
    find_duplicates()
