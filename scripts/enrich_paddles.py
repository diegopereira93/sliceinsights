import sys
from pathlib import Path
from sqlmodel import Session

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import sync_engine
from app.services.enrichment import EnrichmentService

def main():
    service = EnrichmentService()
    
    with Session(sync_engine) as session:
        print("Starting automated technical enrichment...")
        updated_count = service.enrich_all(session)
        print(f"\nSuccessfully enriched {updated_count} paddles.")

if __name__ == "__main__":
    main()
