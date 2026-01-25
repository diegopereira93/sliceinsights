from app.config import Settings
import os

def test_settings():
    os.environ["DATABASE_URL"] = "postgres://user:pass@host:5432/db"
    settings = Settings()
    print(f"Original Environment DATABASE_URL: {os.environ['DATABASE_URL']}")
    print(f"Settings database_url: {settings.database_url}")
    print(f"Settings sync_database_url: {settings.sync_database_url}")

    os.environ["DATABASE_URL"] = "postgresql://user:pass@host:5432/db"
    settings = Settings()
    print(f"\nOriginal Environment DATABASE_URL: {os.environ['DATABASE_URL']}")
    print(f"Settings database_url: {settings.database_url}")
    print(f"Settings sync_database_url: {settings.sync_database_url}")

if __name__ == "__main__":
    test_settings()
