from typing import Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .paddle import PaddleMaster


class MarketOfferBase(SQLModel):
    """Base market offer model with shared attributes."""
    store_name: str
    price_brl: Decimal = Field(decimal_places=2)
    url: str
    is_active: bool = True


class MarketOffer(MarketOfferBase, table=True):
    """MarketOffer database model - Volatile pricing data."""
    __tablename__ = "market_offers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    paddle_id: UUID = Field(foreign_key="paddle_master.id")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    paddle: Optional["PaddleMaster"] = Relationship(back_populates="market_offers")


class MarketOfferRead(SQLModel):
    """Market offer response schema."""
    id: int
    store_name: str
    price_brl: float
    url: str
    last_updated: datetime
    is_active: bool


class MarketOfferCreate(MarketOfferBase):
    """Market offer creation schema."""
    paddle_id: UUID
