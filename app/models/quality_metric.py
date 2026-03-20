from typing import Optional, Dict
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Index


class QualityMetric(SQLModel, table=True):
    __tablename__ = "quality_metrics"

    id: Optional[int] = Field(default=None, primary_key=True)
    scraper_name: str = Field(index=True)
    run_id: str = Field(index=True)
    freshness_hours: float
    completeness_pct: float
    coverage_pct: float
    product_count: int
    error_rate: float
    status: str
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    details: Dict = Field(default={}, sa_column=Column(JSONB))


Index("ix_quality_metrics_scraper_checked", QualityMetric.scraper_name, QualityMetric.checked_at.desc())
