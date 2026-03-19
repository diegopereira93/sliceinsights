# Validation Rules — SliceInsights Data Model

**Extracted from:** app/models/paddle.py, app/models/market_offer.py, app/models/enums.py
**Date:** 2026-03-19

---

## Required Fields (REQUIRED_FIELDS)

These 9 fields must be non-null for a paddle to achieve specs_confidence = 1.0:

| # | Field | Type | Source File | Line |
|---|-------|------|-------------|------|
| 1 | core_thickness_mm | float | paddle.py | 38 |
| 2 | face_material | FaceMaterial enum | paddle.py | 40 |
| 3 | core_material | str | paddle.py | 39 |
| 4 | shape | PaddleShape enum | paddle.py | 41 |
| 5 | swing_weight | int | paddle.py | 44 |
| 6 | spin_rpm | int | paddle.py | 46 |
| 7 | power_rating | int | paddle.py | 54 |
| 8 | handle_length | str | paddle.py | 50 |
| 9 | image_url | str | paddle.py | 63 |

---

## Value Validators

| Field | Constraint | Error Message | Source |
|-------|-----------|---------------|--------|
| power_rating | 0 ≤ value ≤ 10 | "Rating must be between 0 and 10" | paddle.py:23-28 |
| twist_weight | value ≥ 0 | "Twist weight cannot be negative" | paddle.py:30-35 |

---

## specs_confidence Calculation

Defined in `calculate_specs_confidence()` (paddle.py:127-145):

| Condition | Confidence | Description |
|-----------|-----------|-------------|
| validation_sources ≥ 2 | 1.0 | Verified by multiple sources |
| All 9 REQUIRED_FIELDS filled | 1.0 | Complete specs even with 0-1 sources |
| validation_sources == 1 | 0.5 | Single source, incomplete fields |
| No sources, incomplete fields | 0.0 | Unverified and incomplete |

**Current state:** All 86 paddles have `validation_sources: []` (empty) and 8/9 fields NULL → specs_confidence = 0.0 effective, but stored as default 1.0. This indicates the confidence calculation has NOT been re-run after initial seeding.

---

## Derived Ratings

Calculated from raw specs, never fabricated (paddle.py:148-196):

| Rating | Source Field | Formula |
|--------|-------------|---------|
| control_rating | core_thickness_mm | `(thickness - 12) / 7 * 10`, clamped 0-10 |
| spin_rating | spin_rpm | `(rpm - 150) / 150 * 10` if rpm ≥ 150, clamped 0-10 |
| sweet_spot_rating | control_rating (derived) | `10.0 - (control * 0.4)`, clamped 1-10 |
| power_rating | power_rating (direct) | Stored directly, not derived |

---

## Enum Constraints

### FaceMaterial (enums.py:4-9)
| Value | Label |
|-------|-------|
| `carbon` | CARBON |
| `fiberglass` | FIBERGLASS |
| `hybrid` | HYBRID |
| `kevlar` | KEVLAR |

### PaddleShape (enums.py:12-16)
| Value | Label |
|-------|-------|
| `standard` | STANDARD |
| `elongated` | ELONGATED |
| `widebody` | WIDEBODY |

### SkillLevel (enums.py:19-23)
| Value | Label |
|-------|-------|
| `beginner` | BEGINNER |
| `intermediate` | INTERMEDIATE |
| `advanced` | ADVANCED |

### PlayStyle (enums.py:26-30)
| Value | Label |
|-------|-------|
| `power` | POWER |
| `control` | CONTROL |
| `balanced` | BALANCED |

---

## MarketOffer Constraints

| Field | Type | Constraint | Notes |
|-------|------|-----------|-------|
| store_name | str | Required | Identifies scraper source |
| price_brl | Decimal(2) | Required | Brazilian Real price |
| url | str | Required | Product page URL |
| is_active | bool | Default: True | Soft-delete flag |
| last_updated | datetime | Auto-set | `datetime.utcnow` default |
| paddle_id | UUID FK | Must exist in paddle_master | Referential integrity |

---

*Extracted: 2026-03-19 from codebase analysis*
