from enum import Enum


class FaceMaterial(str, Enum):
    """Paddle face material types."""
    CARBON = "carbon"
    FIBERGLASS = "fiberglass"
    HYBRID = "hybrid"
    KEVLAR = "kevlar"


class PaddleShape(str, Enum):
    """Paddle shape types."""
    STANDARD = "standard"
    ELONGATED = "elongated"
    WIDEBODY = "widebody"


class SkillLevel(str, Enum):
    """Player skill levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PlayStyle(str, Enum):
    """Player play styles for recommendations."""
    POWER = "power"
    CONTROL = "control"
    BALANCED = "balanced"
