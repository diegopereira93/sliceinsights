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
    status: str                                     # "pass" | "fail"
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    details: Dict = Field(default={}, sa_column=Column(JSONB))
    # details example: {"breach_count": 3, "oldest_record_id": 42, "scraper": "loja_x"}
