
import asyncio
from sqlmodel import select, func, Session
from app.db.database import sync_engine
from app.models import PaddleMaster

def check_sync():
    print("--- SYNC CHECK ---")
    with Session(sync_engine) as session:
        count = session.exec(select(func.count(PaddleMaster.id))).first()
        print(f"Sync Row Count: {count}")
        first = session.exec(select(PaddleMaster).limit(1)).first()
        print(f"First Paddle: {first.model_name if first else 'None'}")

async def check_async():
    print("\n--- ASYNC CHECK ---")
    # Manually create async session or mock dependency
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlmodel.ext.asyncio.session import AsyncSession
    from app.config import get_settings
    
    settings = get_settings()
    # Use sync url but replace driver? No, use database_url from settings
    # But running inside container vs host?
    # From host, need localhost:5434. 
    # App uses postgres_v3:5432.
    
    # We are running this script FROM HOST.
    # So we must use localhost:5434 for ASYNC too if we want to test that.
    
    url = "postgresql+asyncpg://postgres:postgres@localhost:5434/picklematch"
    engine = create_async_engine(url)
    
    async with AsyncSession(engine) as session:
        result = await session.exec(select(func.count(PaddleMaster.id)))
        count = result.first()
        print(f"Async Row Count (Host): {count}")

if __name__ == "__main__":
    check_sync()
    asyncio.run(check_async())
