from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
from sqlmodel import SQLModel, Field

class PriceAlert(SQLModel, table=True):
    """
    Model for user price alerts.
    Stories users who want to be notified when a paddle's price drops below a target.
    """
    __tablename__ = "price_alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    paddle_id: UUID = Field(foreign_key="paddle_master.id", index=True)
    user_email: str = Field(index=True)
    target_price: Decimal = Field(decimal_places=2)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
