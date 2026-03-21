from typing import Optional, List
from sqlalchemy import ARRAY, String, Column
from sqlmodel import SQLModel, Field


class StoreBase(SQLModel):
    """Base store model with shared attributes."""
    name: str
    slug: Optional[str] = Field(default=None, index=True)
    base_url: str
    is_active: bool = True
    available_brands: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String()))
    )


class Store(StoreBase, table=True):
    """Store database model - Specialized pickleball stores in Brazil."""
    __tablename__ = "stores"
    id: Optional[int] = Field(default=None, primary_key=True)


class StoreRead(StoreBase):
    """Store response schema."""
    id: int


class StoreCreate(StoreBase):
    """Store creation schema."""
    pass
