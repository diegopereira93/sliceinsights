from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String

from .enums import FaceMaterial, PaddleShape

if TYPE_CHECKING:
    from .brand import Brand
    from .market_offer import MarketOffer


from pydantic import field_validator

class PaddleMasterBase(SQLModel):
    """Base paddle model with shared attributes."""
    model_name: str = Field(index=True)
    
    # ... (Model fields are unchanged, inserting methods below) ...

    @field_validator("power_rating")
    @classmethod
    def validate_rating_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 0 or v > 10):
            raise ValueError("Rating must be between 0 and 10")
        return v

    @field_validator("twist_weight")
    @classmethod
    def validate_twist_weight(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Twist weight cannot be negative")
        return v
    
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

    # Performance Ratings (0-10) - Materialized for SQL comparison
    power_rating: Optional[int] = None
    control_rating: Optional[int] = None
    spin_rating: Optional[int] = None
    sweet_spot_rating: Optional[int] = None
    
    # Market Availability
    available_in_brazil: bool = Field(default=False, index=True)  # Produto disponível no Brasil
    
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
    validation_sources: List[str] = Field(
        default=[],
        sa_column=Column(ARRAY(String), nullable=False, server_default="{}")
    )
    specs_confidence: float = Field(default=1.0)


class PaddleRatings(SQLModel):
    """Paddle ratings sub-schema."""
    power: Optional[int] = None
    control: Optional[int] = None
    spin: Optional[int] = None
    sweet_spot: Optional[int] = None


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
    grip_circumference: Optional[str] = None


# ── Data Quality ──────────────────────────────────────────────────────────────

REQUIRED_FIELDS = [
    'core_thickness_mm', 'face_material', 'core_material', 'shape',
    'swing_weight', 'spin_rpm', 'power_rating', 'handle_length',
]


def calculate_specs_confidence(paddle: "PaddleMaster") -> float:
    """Confidence: 1.0 if verified by 2+ sources, 0.5 if 1 source. Fallback to 1.0 if all fields are filled."""
    sources = getattr(paddle, 'validation_sources', [])
    if len(sources) >= 2:
        return 1.0

    all_filled = True
    for field in REQUIRED_FIELDS:
        if getattr(paddle, field, None) is None:
            all_filled = False
            break
            
    if all_filled:
        return 1.0
        
    if len(sources) == 1:
        return 0.5
        
    return 0.0


def calculate_control(core_thickness_mm: Optional[float]) -> Optional[int]:
    """Derive control rating from core thickness (physically grounded: dwell time).

    13mm → 1/10, 14mm → 3/10, 16mm → 6/10, 19mm → 10/10
    """
    if core_thickness_mm is None:
        return None
    control = (core_thickness_mm - 12) / 7 * 10
    return int(round(min(max(control, 0), 10)))


# ── Ratings ───────────────────────────────────────────────────────────────────

def calculate_paddle_ratings(paddle: "PaddleMaster") -> dict:
    """Calculate ratings from REAL data only. Returns None for missing fields — never fabricates."""

    # 1. Control — derived from core_thickness_mm (physically grounded)
    control = calculate_control(paddle.core_thickness_mm)

    # 2. Spin (based on spin_rpm) — REAL DATA ONLY
    spin = None
    spin_rpm = paddle.spin_rpm
    if spin_rpm is not None:
        if spin_rpm >= 150:
            spin = (spin_rpm - 150) / 150 * 10
        else:
            spin = 5.0 if spin_rpm == 0 else 2.0
        spin = int(round(min(max(spin, 0), 10)))

    # 3. Sweet Spot (only calculable if control exists)
    sweet_spot = None
    if control is not None:
        base_sweet = 10.0 - (control * 0.4)
        sweet_spot = int(round(max(1.0, min(10.0, base_sweet))))

    # 4. Power — REAL DATA ONLY
    power = None
    if paddle.power_rating is not None:
        power = int(round(paddle.power_rating))

    has_incomplete_data = any(v is None for v in [power, control, spin])

    return {
        "power": power,
        "control": control,
        "spin": spin,
        "sweet_spot": sweet_spot,
        "has_incomplete_data": has_incomplete_data,
    }


class PaddleRead(SQLModel):
    """Paddle response schema with nested objects."""
    id: UUID
    brand_id: int
    brand_name: Optional[str] = None
    model_name: str
    specs: PaddleSpecs
    ratings: PaddleRatings
    specs_source: str
    specs_confidence: float
    validation_sources: List[str] = []
    is_synthetic: bool = False
    image_url: Optional[str] = None
    is_featured: bool = False
    available_in_brazil: bool = False
    min_price_brl: Optional[float] = None
    offers_count: int = 0

    @classmethod
    def from_paddle(cls, paddle: PaddleMaster, min_price: Optional[float] = None, offers_count: int = 0):
        """Create PaddleRead from PaddleMaster instance."""
        ratings_dict = calculate_paddle_ratings(paddle)
        
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
                power=ratings_dict.get("power"),
                control=ratings_dict.get("control"),
                spin=ratings_dict.get("spin"),
                sweet_spot=ratings_dict.get("sweet_spot"),
            ),
            specs_source=paddle.specs_source,
            specs_confidence=paddle.specs_confidence,
            validation_sources=getattr(paddle, 'validation_sources') or [],
            is_synthetic=ratings_dict.get("is_synthetic", False),
            image_url=paddle.image_url,
            is_featured=paddle.is_featured or False,
            available_in_brazil=paddle.available_in_brazil or False,
            min_price_brl=min_price,
            offers_count=offers_count,
        )


class PaddleCreate(PaddleMasterBase):
    """Paddle creation schema."""
    brand_id: int
    search_keywords: List[str] = []
