# Catalog Feature Specification

## User Story
- As a player, I want to see a list of all available paddles so I can explore my options.
- As a player, I want to filter paddles by skill level, price, and brand to narrow down my search.
- As a player, I want to search for a specific model knowing only part of its name.

## Requirements
- List brands with caching.
- List paddles with pagination and filters (brand, skill, price range, availability).
- Get detailed view of a single paddle with all market offers.
- Fuzzy search functionality.

## Technical Details
### Data Model
- **Brand**: `id`, `name`, `slug`, `logo_url`.
- **PaddleMaster**: `id`, `model_name`, `specs` (JSON), `ratings` (JSON), `skill_level`.
- **MarketOffer**: `id`, `paddle_id`, `price`, `url`, `store_name`.

### API Structure
- `GET /brands`: List all brands.
- `GET /paddles`: List paddles with filters (`limit`, `offset`, `brand_id`, `min_price`, etc.).
- `GET /paddles/{id}`: Detail view including offers.
- `GET /search`: Fuzzy search matching model name, brand, or keywords.

### Implementation Notes
- **Caching**: `TTLCache` used for `/brands` (5 min) and `/paddles` (1 min).
- **Search**: Uses `thefuzz` library for partial ratio matching.
