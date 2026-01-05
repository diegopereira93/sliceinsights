from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String

from .enums import FaceMaterial, PaddleShape, SkillLevel

if TYPE_CHECKING:
    from .brand import Brand
    from .market_offer import MarketOffer


class PaddleMasterBase(SQLModel):
    """Base paddle model with shared attributes."""
    model_name: str = Field(index=True)
    
    # Physical Specs
    core_thickness_mm: Optional[float] = None
    core_material: Optional[str] = None # e.g. "Polymer Honeycomb"
    face_material: Optional[FaceMaterial] = None # e.g. "Carbon"
    shape: Optional[PaddleShape] = None # e.g. "Elongated"
    
    # Advanced Physics Specs (New from verified data)
    swing_weight: Optional[int] = None
    twist_weight: Optional[float] = None
    spin_rpm: Optional[int] = None
    power_original: Optional[float] = None # The exact float from data
    
    # Ergonomics
    handle_length: Optional[str] = None # e.g. "5.5"
    grip_circumference: Optional[str] = None # e.g. "4.125"

    # Performance Ratings (0-10) - Kept for normalized comparison
    power_rating: Optional[int] = None
    
    # Targeting
    image_url: Optional[str] = None
    is_featured: bool = False


class PaddleMaster(PaddleMasterBase, table=True):
    """PaddleMaster database model - Single Source of Truth for paddle specs."""
    __tablename__ = "paddle_master"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    brand_id: int = Field(foreign_key="brands.id")
    search_keywords: List[str] = Field(
        default=[],
        sa_column=Column(ARRAY(String), nullable=False, server_default="{}")
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    brand: Optional["Brand"] = Relationship(back_populates="paddles")
    market_offers: List["MarketOffer"] = Relationship(back_populates="paddle")

    # Data Quality
    specs_source: str = Field(default="manual")
    specs_confidence: float = Field(default=1.0)


class PaddleRatings(SQLModel):
    """Paddle ratings sub-schema."""
    power: Optional[int] = None
    # Synthesized fields will be calculated on read, not stored


class PaddleSpecs(SQLModel):
    """Paddle physical specs sub-schema."""
    core_thickness_mm: Optional[float] = None
    core_material: Optional[str] = None
    face_material: Optional[FaceMaterial] = None
    
    # New Stats
    swing_weight: Optional[int] = None
    twist_weight: Optional[float] = None
    spin_rpm: Optional[int] = None
    power_original: Optional[float] = None
    handle_length: Optional[str] = None


class PaddleRead(SQLModel):
    """Paddle response schema with nested objects."""
    id: UUID
    brand_id: int
    brand_name: Optional[str] = None
    model_name: str
    specs: PaddleSpecs
    ratings: PaddleRatings
    image_url: Optional[str] = None
    is_featured: bool = False
    min_price_brl: Optional[float] = None
    offers_count: int = 0

    @classmethod
    def from_paddle(cls, paddle: PaddleMaster, min_price: Optional[float] = None, offers_count: int = 0):
        """Create PaddleRead from PaddleMaster instance."""
        return cls(
            id=paddle.id,
            brand_id=paddle.brand_id,
            brand_name=paddle.brand.name if paddle.brand else None,
            model_name=paddle.model_name,
            specs=PaddleSpecs(
                core_thickness_mm=paddle.core_thickness_mm,
                core_material=paddle.core_material,
                face_material=paddle.face_material,
                swing_weight=paddle.swing_weight,
                twist_weight=paddle.twist_weight,
                spin_rpm=paddle.spin_rpm,
                power_original=paddle.power_original,
                handle_length=paddle.handle_length,
                grip_circumference=paddle.grip_circumference,
            ),
            ratings=PaddleRatings(
                power=paddle.power_rating,
            ),
            image_url=paddle.image_url,
            is_featured=paddle.is_featured,
            min_price_brl=min_price,
            offers_count=offers_count,
        )


class PaddleCreate(PaddleMasterBase):
    """Paddle creation schema."""
    brand_id: int
    search_keywords: List[str] = []
