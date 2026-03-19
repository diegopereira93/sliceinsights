from typing import Optional, Dict
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class SLOLog(SQLModel, table=True):
    """SLO validation result log entry."""
    __tablename__ = "slo_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    scraper_name: str = Field(index=True)          # e.g. "mercado_livre", "__all__"
    metric_type: str                                # "freshness" | "completeness"
    value_hours: float                              # measured age in hours
    threshold_hours: float                          # configured threshold
    status: str                                     # "pass" | "skip" | "fail"
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    details: Dict = Field(default={}, sa_column=Column(JSONB))
    # details example: {"reason": "recently_updated", "age_hours": 12.5, "newest_record": "2026-03-19T20:00:00+00:00"}
