from typing import AsyncGenerator, Optional
from google.cloud.firestore import AsyncClient, Client
from google.auth import credentials
import os

from app.config import get_settings

settings = get_settings()

_firestore_client: Optional[AsyncClient] = None
_firestore_sync_client: Optional[Client] = None


def get_firestore_credentials():
    """Get Firestore credentials from environment."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        return credentials.Credentials.from_service_account_file(creds_path)
    return credentials.AnonymousCredentials()


async def init_firestore() -> AsyncClient:
    """Initialize Firestore async client."""
    global _firestore_client
    if _firestore_client is None:
        creds = get_firestore_credentials()
        _firestore_client = AsyncClient(credentials=creds)
    return _firestore_client


def init_firestore_sync() -> Client:
    """Initialize Firestore sync client (for scripts)."""
    global _firestore_sync_client
    if _firestore_sync_client is None:
        creds = get_firestore_credentials()
        _firestore_sync_client = Client(credentials=creds)
    return _firestore_sync_client


async def get_firestore() -> AsyncGenerator[AsyncClient, None]:
    """Dependency for getting Firestore client."""
    client = await init_firestore()
    try:
        yield client
    finally:
        pass


def is_firestore_enabled() -> bool:
    """Check if Firestore is enabled in config."""
    return getattr(settings, "use_firestore", False)
