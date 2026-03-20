from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class DeployLog(SQLModel, table=True):
    """DeployLog database model - Tracks deploy batch lifecycle and audit trail."""
    __tablename__ = "deploy_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    batch_id: str = Field(index=True)           # e.g. batch_20260319_2f4a8
    version_id: int
    status: str                                  # pending|validated|published|failed|rolled_back
    scrapers_passed: int
    scrapers_total: int = 11
    products_published: int = 0
    forced: bool = False
    operator_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
