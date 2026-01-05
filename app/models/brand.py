from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .paddle import PaddleMaster


class BrandBase(SQLModel):
    """Base brand model with shared attributes."""
    name: str = Field(index=True, unique=True)
    website: Optional[str] = None


class Brand(BrandBase, table=True):
    """Brand database model."""
    __tablename__ = "brands"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    paddles: List["PaddleMaster"] = Relationship(back_populates="brand")


class BrandRead(BrandBase):
    """Brand response schema."""
    id: int


class BrandCreate(BrandBase):
    """Brand creation schema."""
    pass
