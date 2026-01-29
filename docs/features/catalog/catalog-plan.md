# Catalog Feature Plan

## Goal
Provide a comprehensive and searchable catalog of pickleball paddles available in the Brazilian market, organized by brand and specifications.

## Core Concept
The catalog serves as the foundation of the platform, aggregating data from multiple stores (handled by scrapers/seeders) and presenting it in a unified, normalized format. It enables users to browse, filter, and search for equipment.

## Proposed Solution
- **Centralized Database**: Store normalized data in `Brand` and `PaddleMaster` tables.
- **Market Offers**: Separate specific store offers (`MarketOffer`) from the master product data to allow price comparison.
- **High Performance API**: Use caching (`TTLCache`) and optimized database queries (avoiding N+1 problems) for fast listing.
- **Fuzzy Search**: Implement `thefuzz` for flexible search capabilities across brands and models.

## Success Metrics
- API Response time < 200ms for list endpoints.
- Search accuracy (users find intended product).
- Up-to-date pricing (synced via scrapers).
