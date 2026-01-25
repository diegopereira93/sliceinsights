#!/usr/bin/env python3
"""
Script to enrich paddle specs from paddle_stats_dump.csv.
Matches paddles by brand + model name using fuzzy matching.
"""
import csv
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from thefuzz import fuzz
from dotenv import load_dotenv

load_dotenv()

# Configuration
CSV_PATH = "data/raw/paddle_stats_dump.csv"
MIN_MATCH_SCORE = 75  # Minimum fuzzy match score to consider a match

# Column mappings from CSV (0-indexed)
COL_BRAND = 0
COL_MODEL = 1
COL_SWING_WEIGHT = 3
COL_TWIST_WEIGHT = 4
COL_SPIN_RPM = 5
COL_POWER = 6
COL_CORE_THICKNESS = 7
COL_SHAPE = 11
COL_FACE_MATERIAL = 12
COL_CORE_MATERIAL = 14


def safe_float(value):
    """Convert value to float, return None if invalid."""
    if not value or value == '' or value == 'N/A':
        return None
    try:
        # Remove any non-numeric characters except . and -
        cleaned = ''.join(c for c in str(value) if c.isdigit() or c in '.-')
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None


def safe_int(value):
    """Convert value to int, return None if invalid."""
    f = safe_float(value)
    return int(f) if f is not None else None


def load_csv_specs():
    """Load paddle specs from CSV file."""
    specs = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if len(row) < 15:  # Ensure enough columns
                continue
            specs.append({
                'brand': row[COL_BRAND].strip() if row[COL_BRAND] else '',
                'model': row[COL_MODEL].strip() if row[COL_MODEL] else '',
                'swing_weight': safe_int(row[COL_SWING_WEIGHT]) if len(row) > COL_SWING_WEIGHT else None,
                'twist_weight': safe_float(row[COL_TWIST_WEIGHT]) if len(row) > COL_TWIST_WEIGHT else None,
                'spin_rpm': safe_int(row[COL_SPIN_RPM]) if len(row) > COL_SPIN_RPM else None,
                'power_rating': safe_int(safe_float(row[COL_POWER])) if len(row) > COL_POWER else None,
                'core_thickness_mm': safe_float(row[COL_CORE_THICKNESS]) if len(row) > COL_CORE_THICKNESS else None,
                'shape': row[COL_SHAPE].strip() if len(row) > COL_SHAPE and row[COL_SHAPE] else None,
                'face_material': row[COL_FACE_MATERIAL].strip() if len(row) > COL_FACE_MATERIAL and row[COL_FACE_MATERIAL] else None,
                'core_material': row[COL_CORE_MATERIAL].strip() if len(row) > COL_CORE_MATERIAL and row[COL_CORE_MATERIAL] else None,
            })
    return specs


def find_best_match(brand: str, model: str, csv_specs: list) -> tuple:
    """Find the best matching paddle in CSV by brand + model."""
    best_score = 0
    best_match = None
    
    search_str = f"{brand} {model}".lower().strip()
    
    for spec in csv_specs:
        csv_str = f"{spec['brand']} {spec['model']}".lower().strip()
        
        # Try different matching strategies
        score1 = fuzz.ratio(search_str, csv_str)
        score2 = fuzz.partial_ratio(search_str, csv_str)
        score3 = fuzz.token_set_ratio(search_str, csv_str)
        
        score = max(score1, score2, score3)
        
        if score > best_score:
            best_score = score
            best_match = spec
    
    return best_match, best_score


def main():
    print("=" * 60)
    print("Paddle Specs Enrichment Script (ORM Secure Version)")
    print("=" * 60)
    
    # Load CSV specs
    print(f"\n1. Loading specs from {CSV_PATH}...")
    csv_specs = load_csv_specs()
    print(f"   Loaded {len(csv_specs)} paddles from CSV")
    
    # Init sync DB
    from app.db.database import init_db_sync, sync_engine
    from sqlmodel import Session, select
    from app.models import PaddleMaster, Brand
    
    # Force connection string if needed, but prefer env
    # db_url = os.getenv("DATABASE_URL") 
    
    print("\n2. Connecting to database...")
    init_db_sync()
    
    updated = 0
    not_found = []
    
    with Session(sync_engine) as session:
        # Get paddles from database
        print("\n3. Fetching paddles from database...")
        # Join with Brand to get brand name efficiently
        statement = select(PaddleMaster, Brand).join(Brand)
        results = session.exec(statement).all()
        
        print(f"   Found {len(results)} paddles in database")
        
        # Match and update
        print("\n4. Matching and updating specs...")
        
        for paddle, brand in results:
            match, score = find_best_match(brand.name, paddle.model_name, csv_specs)
            
            if match and score >= MIN_MATCH_SCORE:
                # Update attributes pythonically (ORM handles safety)
                changes_made = False
                
                if match['swing_weight'] is not None and paddle.swing_weight != match['swing_weight']:
                    paddle.swing_weight = match['swing_weight']
                    changes_made = True
                
                if match['twist_weight'] is not None and paddle.twist_weight != match['twist_weight']:
                    paddle.twist_weight = match['twist_weight']
                    changes_made = True
                
                if match['spin_rpm'] is not None and paddle.spin_rpm != match['spin_rpm']:
                    paddle.spin_rpm = match['spin_rpm']
                    changes_made = True
                
                if match['power_rating'] is not None and paddle.power_rating != match['power_rating']:
                    paddle.power_rating = match['power_rating']
                    changes_made = True
                    
                if match['core_thickness_mm'] is not None and paddle.core_thickness_mm != match['core_thickness_mm']:
                    paddle.core_thickness_mm = match['core_thickness_mm']
                    changes_made = True
                    
                if match['core_material'] is not None and paddle.core_material != match['core_material']:
                    paddle.core_material = match['core_material']
                    changes_made = True

                if changes_made:
                    session.add(paddle)
                    updated += 1
                    print(f"   ✓ {brand.name} {paddle.model_name} -> {match['brand']} {match['model']} (score: {score})")
            else:
                not_found.append((brand.name, paddle.model_name, score))
                # print(f"   ✗ {brand.name} {paddle.model_name} (best score: {score})")
        
        session.commit()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total paddles in DB: {len(results)}")
    print(f"Successfully matched/updated: {updated}")
    print(f"Not found: {len(not_found)}")
    
    if not_found:
        print("\nPaddles without matches:")
        for brand, model, score in not_found:
            print(f"  - {brand} {model} (best score: {score})")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
