from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/picklematch"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/picklematch"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # App
    app_name: str = "SliceInsights"
    app_version: str = "1.0.0"
    
    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8002"]
    
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
