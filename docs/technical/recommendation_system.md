# Recommendation System Logic

This document details the technical implementation of the SliceInsights recommendation engine, including rating synthesis, ranking formulas, and value score calculation.

## 1. Unified Rating Synthesis

To ensure consistency between the recommendation engine and the user interface, all paddle ratings are synthesized from raw physical specifications using a centralized function `calculate_paddle_ratings`.

All ratings are normalized to a **0.0 - 10.0 scale**.

### Control (Stability)
The control rating is derived from `twist_weight`. The system handles two different data scales:
- **Large Scale (Degrees)**: If `twist_weight > 100` (typically 150-600).
  - Formula: `(twist_weight - 150) / 450 * 10`
- **Small Scale (Proxy)**: If `twist_weight <= 100` (typically 5.0-7.5).
  - Formula: `twist_weight * 1.5`
- **Constraints**: Minimum 0.0, Maximum 10.0.

### Spin
The spin rating is derived from `spin_rpm`.
- **Primary Range**: 150 - 300 (standardized from raw RPM values in current dump).
- **Formula**: `(spin_rpm - 150) / 150 * 10`
- **Missing Data**: Defaults to 5.0 if `spin_rpm == 0`.

### Power
The power rating is currently based on a pre-calculated `power_rating` field in the database (0-10).
- **Default**: 5.0 if missing.

### Sweet Spot (Forgiveness)
The sweet spot is synthesized inversely from the stability/control rating to represent technical trade-offs.
- **Formula**: `max(1.0, 10.0 - (control * 0.4))`

---

## 2. Ranking Strategy

The recommendation engine uses a multi-stage approach to find the best paddles for a user profile.

### Hard Filters (SQL Level)
1. **Tennis Elbow**: If `has_tennis_elbow` is true, only paddles with `core_thickness_mm >= 16.0` are selected.
2. **Budget**: Only paddles with a minimum market price ≤ `budget_max_brl` are selected.
3. **Weight Preference**:
   - `light`: `swing_weight <= 110`
   - `standard`: `swing_weight` between 110 and 120
   - `heavy`: `swing_weight >= 120`

### Smart Scoring (Python Level)
After filtering, paddles are scored based on the user's `play_style`:

| Style | Scoring Formula |
|-------|-----------------|
| **POWER** | `(Power * 0.8) + (Control * 0.2)` |
| **CONTROL** | `(Control * 0.8) + (Power * 0.2)` |
| **BALANCED** | `(Power + Control) / 2` |

**Slider Preference**: If the user provides a specific `power_preference_percent` (0-100%), the weights are adjusted linearly.

---

## 3. Value Score Calculation

The `value_score` helps users identify "best deals" by comparing technical performance to market price.

- **Performance Aggregate**: `(Power + Control + Spin) / 3`
- **Formula**: `(Performance Aggregate / Price) * 1000`
- **Interpretation**: A higher score (e.g., > 8.0) indicates a paddle that offers high performance relative to its price in BRL.

---

## 4. Match Reasons and Tags

The engine generates dynamic natural language reasons for each recommendation:
- **Excepcional potência**: Power rating ≥ 8.
- **Máxima estabilidade**: Control rating ≥ 8.
- **Equilíbrio ideal**: Average of Power/Control ≥ 7.5 (for BALANCED style).
- **Conforto**: 16mm core for tennis elbow users.

Tags like **"Top Pick"**, **"Spin Machine"**, and **"Elite Control"** are applied based on top rankings and metric thresholds (≥ 9.0).
