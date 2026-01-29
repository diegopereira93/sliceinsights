# Recommendation Engine Specification

## User Story
- As a beginner, I want suggestions for paddles that are forgiving and easy to control.
- As a player with tennis elbow, I want to see only paddles that are known to be arm-friendly.

## Requirements
- Input: customizable user profile (skill, budget, style, injuries).
- Output: ranked list of paddles with reasoning.
- Logic:
    - Tennis Elbow -> Filter out heavy/stiff paddles.
    - Power Style -> Prioritize high swing weight/power rating.
    - Control Style -> Prioritize high twist weight/sweet spot.

## Technical Details
### Data Model
- **UserProfile**: Temporary schema for request body (not persisted in DB currently).

### API Structure
- `POST /recommendations`: Accepts `UserProfile`, returns list of `PaddleRead` with internal scoring.

### Algorithm
- `RecommendationEngine` service class handles the logic.
- Fetches all candidate paddles.
- Applies filters (hard constraints).
- Computes weighted score based on attributes.
- Returns top K results.
