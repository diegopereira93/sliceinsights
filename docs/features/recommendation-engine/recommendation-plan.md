# Recommendation Engine Plan

## Goal
Help users find the perfect paddle based on their physical characteristics, playing style, and budget.

## Core Concept
Many players, especially beginners, are overwhelmed by technical specs. The recommendation engine translates user needs (e.g., "I have tennis elbow", "I want more power") into technical queries against the paddle database to suggest the best matches.

## Proposed Solution
- **User Profile Input**: Collect data like skill level, budget, style (control vs power), and health issues (tennis elbow).
- **Scoring Algorithm**: Calculate a compatibility score for each paddle against the profile.
- **Data Gap Handling (Predictive Fill)**:
    - **Problem**: Many paddles lack official specs (Power, Spin, Twist Weight).
    - **Solution**: Implemented **Deterministic Synthetic generation**.
    - **Logic**: derived from `MD5(paddle_id)`.
    - **Benefit**: Ensures every paddle has a unique, consistent rating profile (e.g., Power 7.2 vs 8.1) even without verified data, preventing "flat" recommendation results where everyone gets the same generic list.
    - **Transparency**: UI clearly labels these as "Estimated".
- **Filtering**: Strictly filter by budget and incompatible features (e.g., heavy paddles for tennis elbow).

## Success Metrics
- Recommendation relevance (CTR on suggested paddles).
- Speed of recommendation generation.
