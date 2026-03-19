from typing import Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
from sqlmodel import SQLModel, Field


class SLOAlert(SQLModel, table=True):
    """Deduplication state for SLO breach alerts."""
    __tablename__ = "slo_alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    scraper_name: str = Field(index=True)
    metric_type: str  # "freshness" | "completeness"
    last_alert_time: datetime
    status: str = Field(default="active")  # "active" | "resolved"
    alert_count: int = Field(default=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SLOBreach:
    """Represents a detected SLO breach ready for alerting."""
    scraper_name: str
    metric_type: str  # "freshness" | "completeness"
    value_hours: float
    threshold_hours: float
    checked_at: str  # ISO 8601 UTC string
    last_record_time: str | None  # ISO 8601 UTC or None
    details: dict = field(default_factory=dict)

    @property
    def severity(self) -> str:
        """Derive P1/P2/P3 severity from metric_type."""
        if self.metric_type == "freshness":
            return "P1"
        elif self.metric_type == "completeness":
            return "P2"
        return "P3"
