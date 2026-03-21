"""
Database initialization script for Phase 1 audit testing.

Resets the test database (picklematch) to a fresh state:
- Drops existing tables
- Creates fresh schema
- Seeds minimal test data if needed

Usage:
  python scripts/test_db_init.py              # Reset to clean state
  python scripts/test_db_init.py --seed       # Include minimal seed data
  python scripts/test_db_init.py --dry-run    # Show what would happen
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# SQL for creating core audit tables directly (no ORM dependency)
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS paddle_master (
    id SERIAL PRIMARY KEY,
    brand VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    specs_confidence FLOAT DEFAULT 0.0,
    source VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
"""

DROP_TABLE_SQL = """
DROP TABLE IF EXISTS paddle_master CASCADE;
"""


def init_test_db(seed=False, dry_run=False):
    """
    Reset test database to clean state.

    Args:
        seed: If True, add minimal test data
        dry_run: If True, print SQL without executing

    Returns:
        dict with status: "success", "error", or "dry-run"
    """
    print(f"[{datetime.utcnow().isoformat()}] Initializing test database...")

    # Use test database URL
    db_url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@postgres_v3:5432/picklematch"
    )

    print(f"  Database URL: {db_url}")

    if dry_run:
        print("  [DRY RUN] Would execute:")
        print("    1. DROP TABLE IF EXISTS paddle_master CASCADE")
        print("    2. CREATE TABLE paddle_master (...)")
        if seed:
            print("    3. INSERT INTO paddle_master (brand, model, ...) VALUES ('TestPaddle', 'Test-01', ...)")
        return {"status": "dry-run", "message": "No changes applied"}

    try:
        # Try SQLModel/SQLAlchemy approach first
        try:
            from sqlmodel import create_engine, SQLModel

            engine = create_engine(db_url, echo=False)

            print("  Dropping existing tables...")
            SQLModel.metadata.drop_all(engine)

            print("  Creating fresh schema...")
            SQLModel.metadata.create_all(engine)

            if seed:
                print("  Seeding test data...")
                _seed_with_sqlmodel(engine)

        except ImportError:
            # Fallback: use psycopg2 directly
            import psycopg2
            conn = psycopg2.connect(db_url)
            conn.autocommit = True
            cur = conn.cursor()

            print("  Dropping existing tables...")
            cur.execute(DROP_TABLE_SQL)

            print("  Creating fresh schema...")
            cur.execute(CREATE_TABLE_SQL)

            if seed:
                print("  Seeding test data...")
                _seed_with_psycopg2(cur)

            cur.close()
            conn.close()

        print(f"[{datetime.utcnow().isoformat()}] Database initialization complete")
        return {"status": "success", "message": "Test database reset"}

    except Exception as e:
        return {
            "status": "error",
            "message": f"Database initialization failed: {str(e)}",
            "db_url": db_url,
        }


def _seed_with_sqlmodel(engine):
    """Insert minimal test data using SQLModel session."""
    try:
        from sqlmodel import Session
        from app.models import PaddleMaster

        with Session(engine) as session:
            test_paddle = PaddleMaster(
                brand="TestPaddle",
                model="Test-01",
                specs_confidence=1.0,
                source="test_db_init.py",
            )
            session.add(test_paddle)
            session.commit()
            print("    Added 1 test paddle record")
    except ImportError as e:
        print(f"    Warning: Could not seed via SQLModel: {e}")


def _seed_with_psycopg2(cursor):
    """Insert minimal test data using psycopg2 cursor."""
    cursor.execute(
        """
        INSERT INTO paddle_master (brand, model, specs_confidence, source)
        VALUES (%s, %s, %s, %s)
        """,
        ("TestPaddle", "Test-01", 1.0, "test_db_init.py"),
    )
    print("    Added 1 test paddle record")


def main():
    parser = argparse.ArgumentParser(
        description="Reset test database to fresh state for audit testing"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed minimal test data after reset"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes"
    )

    args = parser.parse_args()

    result = init_test_db(seed=args.seed, dry_run=args.dry_run)

    if result["status"] in ("success", "dry-run"):
        print(f"[OK] {result['message']}")
        return 0
    else:
        print(f"[FAIL] {result['message']}")
        if "note" in result:
            print(f"  {result['note']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
