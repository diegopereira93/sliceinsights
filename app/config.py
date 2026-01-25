from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    # Railway provides DATABASE_URL, but SQLAlchemy async needs postgresql+asyncpg://
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/picklematch",
        alias="DATABASE_URL"
    )
    database_url_sync: Optional[str] = Field(
        default=None,
        alias="DATABASE_URL_SYNC"
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_async_db_url(cls, v: str) -> str:
        """Ensure the database URL uses the asyncpg driver."""
        if not v:
            return v
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            
        # Fix for asyncpg: replace sslmode with ssl as asyncpg doesn't support sslmode
        # but supports ssl=require in the query string (parsed by SQLAlchemy)
        if "sslmode=" in v:
            v = v.replace("sslmode=", "ssl=")
            
        return v

    @property
    def sync_database_url(self) -> str:
        """Get a synchronous version of the database URL."""
        if self.database_url_sync:
            return self.database_url_sync
        
        # Fallback to transforming database_url
        v = self.database_url
        if "+asyncpg" in v:
            return v.replace("+asyncpg", "")
        return v
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # App
    app_name: str = "SliceInsights"
    app_version: str = "1.0.0"
    
    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8002"]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse allowed origins from JSON string or list."""
        if isinstance(v, str) and v.startswith("["):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v.split(",")
        elif isinstance(v, str):
            return v.split(",")
        return v
    
    # Logging
    log_level: str = "INFO"
    
    # Observability (optional)
    sentry_dsn: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
