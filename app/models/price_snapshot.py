from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlmodel import SQLModel, Field, Relationship

class PriceSnapshot(SQLModel, table=True):
    """
    PriceSnapshot database model - Historical pricing data for time-series analysis.
    This table stores a snapshot of a paddle's price at a specific point in time.
    """
    __tablename__ = "price_snapshots"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    paddle_id: UUID = Field(foreign_key="paddle_master.id", index=True)
    store_name: str = Field(index=True)
    price_brl: Decimal = Field(decimal_places=2)
    url: str
    snapshot_date: str = Field(index=True) # Format: YYYY-MM-DD for easier querying
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Optional metadata from scraper
    currency: str = Field(default="BRL")
    is_available: bool = Field(default=True)
