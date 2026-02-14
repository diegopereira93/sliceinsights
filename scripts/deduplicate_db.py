
import logging
from sqlmodel import Session, select, func
from app.db.database import sync_engine
from app.models import Brand, PaddleMaster, MarketOffer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def deduplicate_database():
    with Session(sync_engine) as session:
        # 1. Deduplicate Brands (Case-Insensitive)
        print("\n🔍 Checking for duplicate brands...")
        brand_names_sq = select(func.lower(Brand.name)).group_by(func.lower(Brand.name)).having(func.count(Brand.id) > 1)
        duplicate_brand_names = session.exec(brand_names_sq).all()
        
        for name_lower in duplicate_brand_names:
            brands = session.exec(select(Brand).where(func.lower(Brand.name) == name_lower)).all()
            # Keep the one with the shortest name (usually the most canonical) or just the first one
            primary_brand = brands[0]
            duplicates = brands[1:]
            
            print(f"  Fixing brand: '{primary_brand.name}' (Merging {len(duplicates)} duplicates)")
            
            for dup in duplicates:
                # Re-assign paddles from duplicate brand to primary brand
                paddles_to_reassign = session.exec(select(PaddleMaster).where(PaddleMaster.brand_id == dup.id)).all()
                for paddle in paddles_to_reassign:
                    paddle.brand_id = primary_brand.id
                    session.add(paddle)
                
                session.flush() # Ensure FKs are updated before deletion
                session.delete(dup)
        
        session.commit()
        print("✅ Brand deduplication complete.")

        # 2. Deduplicate Paddles (Same brand + same model name)
        print("\n🔍 Checking for duplicate paddles...")
        paddle_keys_sq = select(PaddleMaster.model_name, PaddleMaster.brand_id).group_by(PaddleMaster.model_name, PaddleMaster.brand_id).having(func.count(PaddleMaster.id) > 1)
        duplicate_paddle_keys = session.exec(paddle_keys_sq).all()
        
        for model_name, brand_id in duplicate_paddle_keys:
            paddles = session.exec(select(PaddleMaster).where(
                PaddleMaster.model_name == model_name,
                PaddleMaster.brand_id == brand_id
            )).all()
            
            # Prefer the one with specifications or available_in_brazil=True
            paddles.sort(key=lambda p: (p.available_in_brazil, p.specs_confidence or 0, p.created_at), reverse=True)
            
            primary_paddle = paddles[0]
            duplicates = paddles[1:]
            
            print(f"  Fixing paddle: '{model_name}' (Brand ID: {brand_id}) - Merging {len(duplicates)} duplicates")
            
            for dup in duplicates:
                # Re-assign market offers
                offers_to_reassign = session.exec(select(MarketOffer).where(MarketOffer.paddle_id == dup.id)).all()
                for offer in offers_to_reassign:
                    offer.paddle_id = primary_paddle.id
                    session.add(offer)
                
                session.delete(dup)
        
        session.commit()
        print("✅ Paddle deduplication complete.")

if __name__ == "__main__":
    deduplicate_database()
