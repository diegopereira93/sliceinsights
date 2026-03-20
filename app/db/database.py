from typing import AsyncGenerator
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models.slo import SLOLog  # noqa: F401 — registers SLOLog with SQLModel metadata
from app.models.slo_alert import SLOAlert  # noqa: F401 — registers SLOAlert with SQLModel metadata
from app.models.deploy_log import DeployLog  # noqa: F401 — registers DeployLog with SQLModel metadata

settings = get_settings()

# Async engine for FastAPI
async_engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# Sync engine for Alembic migrations and seed scripts
sync_engine = create_engine(
    settings.sync_database_url,
    echo=settings.debug,
)

# Async session factory
async_session_maker = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables and sync missing columns."""
    async with async_engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.run_sync(_sync_missing_columns)


def init_db_sync():
    """Initialize database tables synchronously (for scripts)."""
    from sqlalchemy import text
    with sync_engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    SQLModel.metadata.create_all(sync_engine)
    with sync_engine.begin() as conn:
        _sync_missing_columns(conn)


def _sync_missing_columns(conn):
    """Detect and add missing columns to existing tables.
    
    SQLModel.metadata.create_all only creates missing TABLES, not missing COLUMNS.
    This function bridges that gap by inspecting existing tables and adding
    any columns defined in the models but absent from the database.
    """
    from sqlalchemy import inspect, text, String, Float, Integer, Boolean
    
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    type_map = {
        "VARCHAR": "VARCHAR",
        "TEXT": "VARCHAR",
        "FLOAT": "FLOAT",
        "DOUBLE": "FLOAT",
        "DOUBLE PRECISION": "FLOAT",
        "INTEGER": "INTEGER",
        "BIGINT": "INTEGER",
        "BOOLEAN": "BOOLEAN",
        "TIMESTAMP WITHOUT TIME ZONE": "TIMESTAMP",
        # Default fallback for ARRAY types if not matched by logic below
        "ARRAY": "VARCHAR[]",
    }
    
    for table in SQLModel.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
            
        existing_cols = {col["name"] for col in inspector.get_columns(table.name)}
        
        for column in table.columns:
            if column.name in existing_cols:
                continue
            
            # Map SQLAlchemy type to SQL type string
            col_type = str(column.type).upper()
            
            # Robust mapping for ARRAY types
            if "ARRAY" in col_type:
                sql_type = "VARCHAR[]"
            else:
                sql_type = type_map.get(col_type, col_type)
            
            # Build default clause
            default_clause = ""
            if column.default is not None:
                default_val = getattr(column.default, 'arg', None)
                if isinstance(default_val, bool):
                    default_clause = f" DEFAULT {'TRUE' if default_val else 'FALSE'}"
                elif isinstance(default_val, (int, float)):
                    default_clause = f" DEFAULT {default_val}"
                elif isinstance(default_val, str):
                    default_clause = f" DEFAULT '{default_val}'"
            
            sql = f'ALTER TABLE "{table.name}" ADD COLUMN IF NOT EXISTS "{column.name}" {sql_type}{default_clause}'
            try:
                # Use a nested transaction (SAVEPOINT) to isolate this ALTER TABLE
                # This ensures that if the syntax is wrong, it doesn't abort the global transaction
                with conn.begin_nested():
                    conn.execute(text(sql))
            except Exception:
                # Column might already exist or type might be complex (e.g. Vector)
                # We skip and let the application handle potential missing column errors later
                pass

