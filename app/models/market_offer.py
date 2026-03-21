from typing import Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .paddle import PaddleMaster
    from .store import Store


class MarketOfferBase(SQLModel):
    """Base market offer model with shared attributes."""
    store_id: int = Field(foreign_key="stores.id")
    price_brl: Decimal = Field(decimal_places=2)
    url: str
    is_active: bool = True


class MarketOffer(MarketOfferBase, table=True):
    """MarketOffer database model - Volatile pricing data."""
    __tablename__ = "market_offers"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    paddle_id: UUID = Field(foreign_key="paddle_master.id")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    version_id: Optional[int] = None

    # Relationships
    paddle: Optional["PaddleMaster"] = Relationship(back_populates="market_offers")
    store: Optional["Store"] = Relationship()


class MarketOfferRead(SQLModel):
    """Market offer response schema."""
    id: int
    store_id: int
    price_brl: float
    url: str
    last_updated: datetime
    is_active: bool
    version_id: Optional[int] = None


class MarketOfferCreate(MarketOfferBase):
    """Market offer creation schema."""
    paddle_id: UUID
