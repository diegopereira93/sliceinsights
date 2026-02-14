from app.models.paddle import PaddleMaster, calculate_paddle_ratings

import asyncio
import sys
import os
from uuid import uuid4

# Add app to path
sys.path.append(os.getcwd())

async def verify_variety():
    print("--- Verifying Recommendation Variety ---")
    
    # Create 3 dummy paddles with NO specs (simulating current DB state)
    paddles = []
    base_names = ["Paddle A", "Paddle B", "Paddle C"]
    for i, name in enumerate(base_names):
        p = PaddleMaster(
            id=uuid4(),
            brand_id=1,
            model_name=name,
            # ALL SPECS NULL
            core_thickness_mm=None,
            twist_weight=None,
            spin_rpm=None,
            power_rating=None
        )
        paddles.append(p)
        
    print(f"Created {len(paddles)} dummy paddles with NULL specs.")
    
    # Calculate ratings for each
    results = []
    for p in paddles:
        ratings = calculate_paddle_ratings(p)
        print(f"\nPaddle: {p.model_name} (ID: {p.id})")
        print(f"Ratings: {ratings}")
        results.append(ratings)
        
    # Verification 1: Are they different?
    unique_powers = set(r['power'] for r in results)
    unique_controls = set(r['control'] for r in results)
    
    if len(unique_powers) > 1 or len(unique_controls) > 1:
        print("\n✅ SUCCESS: Ratings are varied based on ID/Name hash.")
    else:
        print("\n❌ FAILURE: Ratings are identical.")
        sys.exit(1)

    # Verification 2: Deterministic?
    print("\n--- Verifying Determinism ---")
    p1 = paddles[0]
    r1 = calculate_paddle_ratings(p1)
    r2 = calculate_paddle_ratings(p1)
    
    if r1 == r2:
        print(f"✅ SUCCESS: Ratings are deterministic. {r1} == {r2}")
    else:
        print(f"❌ FAILURE: Ratings changed for same paddle! {r1} != {r2}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify_variety())
