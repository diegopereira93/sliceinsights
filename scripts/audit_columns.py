import os
import pandas as pd
from sqlalchemy import create_engine

# Use the internal docker URL by default, but allow override
DATABASE_URL = os.getenv("DATABASE_URL_SYNC", "postgresql://postgres:postgres@postgres_v3:5432/picklematch")

def audit_columns():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        engine = create_engine(DATABASE_URL)
        
        # Determine table columns first to handle potential schema changes dynamically
        # or just select *
        query = "SELECT * FROM paddle_master"
        
        df = pd.read_sql(query, engine)
        
        total_rows = len(df)
        print(f"\n📊 TOTAL PADDLES: {total_rows}")
        print("=" * 65)
        print(f"{'COLUMN':<30} | {'FILL RATE':<10} | {'MISSING':<8} | {'EXAMPLE'}")
        print("-" * 65)
        
        stats = []
        for col in df.columns:
            non_null = df[col].count()
            fill_rate = (non_null / total_rows) * 100
            missing = total_rows - non_null
            
            # Get a non-null example
            example = df[col].dropna().iloc[0] if non_null > 0 else "N/A"
            example_str = str(example)[:20] + "..." if len(str(example)) > 20 else str(example)
            
            stats.append((col, fill_rate, missing, example_str))
        
        # Sort by fill rate ascending (problematic ones first)
        stats.sort(key=lambda x: x[1])
        
        for col, rate, miss, ex in stats:
            color = ""
            if rate == 100:
                status = "✅"
            elif rate > 80:
                status = "⚠️" 
            else:
                status = "❌"
                
            print(f"{status} {col:<28} | {rate:6.2f}%    | {miss:<8} | {ex}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    audit_columns()
