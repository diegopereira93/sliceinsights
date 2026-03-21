---
phase: 14-web-catalog-page
plan: 01
subsystem: ui
tags: [nextjs, typescript, catalog, paddle, react]

# Dependency graph
requires: []
provides:
  - CatalogPaddle, CatalogOffer, CatalogStore, CatalogFilters, CatalogResponse TypeScript types
  - Backend image_url field in GET /catalog/paddles response
  - CatalogPaddleCard with glass-card, badges, price, and store CTA
  - SkeletonGrid with 6 shimmer placeholder cards
  - CatalogGrid with loading/empty/error states
  - CatalogPagination with Anterior/Proxima navigation
affects: [14-web-catalog-page]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - glass-card + framer-motion entrance animation for catalog cards
    - Skeleton grid pattern with bg-muted animate-pulse shimmer
    - Responsive grid: grid-cols-1 sm:grid-cols-2 lg:grid-cols-3
    - ExternalLink icon + new tab for store CTA

key-files:
  created:
    - frontend/types/catalog.ts
    - frontend/components/catalog/catalog-paddle-card.tsx
    - frontend/components/catalog/catalog-grid.tsx
    - frontend/components/catalog/catalog-pagination.tsx
  modified:
    - app/api/endpoints/catalog.py

key-decisions:
  - "Used plain <img> instead of next/image to avoid remote hostname config (multiple store domains)"
  - "CatalogGrid delegates to SkeletonGrid/EmptyState/real cards based on isLoading/isError/total state"

patterns-established:
  - "CatalogPaddleCard follows glass-card pattern from UI-SPEC with motion.div entrance animation"
  - "SkeletonGrid renders exactly 6 cards matching card proportions for loading state"

requirements-completed: [WEB-01]

# Metrics
duration: 4min
completed: 2026-03-21
---

# Phase 14 Plan 01: Web Catalog Page — Foundational Types & Presentational Components

**CatalogPaddle types, backend image_url fix, and three presentational components (CatalogPaddleCard, CatalogGrid with SkeletonGrid, CatalogPagination)**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-21T19:49:01Z
- **Completed:** 2026-03-21T19:53:00Z
- **Tasks:** 2
- **Files created:** 4
- **Files modified:** 1

## Accomplishments
- Created `frontend/types/catalog.ts` with all catalog-specific TypeScript types matching the API response shape
- Fixed backend `catalog.py` to include `image_url` field in GET /catalog/paddles response (1-line addition)
- Built `CatalogPaddleCard` with glass-card pattern, brand/thickness/surface badges, "A partir de R$" price, and "Ver na [StoreName]" CTA opening in new tab
- Built `CatalogGrid` with SkeletonGrid (6 shimmer cards), EmptyState (search/wifi-off), and loaded grid states
- Built `CatalogPagination` with Anterior/Proxima buttons, page indicator, and proper disabled states

## Task Commits

Each task was committed atomically:

1. **Task 1: Create CatalogPaddle types and fix backend image_url gap** - `ef3364e` (feat)
2. **Task 2: Build CatalogPaddleCard, CatalogGrid, CatalogPagination** - `f873a6c` (feat)

**Plan metadata:** docs commit (pending)

## Files Created/Modified
- `frontend/types/catalog.ts` - CatalogPaddle, CatalogOffer, CatalogStore, CatalogFilters, CatalogResponse, CatalogStoresResponse type exports
- `frontend/components/catalog/catalog-paddle-card.tsx` - Glass-card with image, badges, price, and store CTA
- `frontend/components/catalog/catalog-grid.tsx` - SkeletonGrid (6 shimmer) + CatalogGrid with state delegation
- `frontend/components/catalog/catalog-pagination.tsx` - Anterior/Proxima pagination with disabled states
- `app/api/endpoints/catalog.py` - Added `image_url: paddle.image_url` to paddle response dict

## Decisions Made
- Used plain `<img loading="lazy">` instead of `next/image` to avoid remote hostname configuration for multiple store domains
- `CatalogGrid` returns null pagination when `totalPages <= 1` (hides pagination bar on single-page results)
- Brand badge only renders when `paddle.brand` is truthy; surface material badge only renders when `paddle.specs.surface_material` is truthy
- Price and CTA only render when `cheapestOffer` exists (paddles with no active offers show no price)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Types and all presentational components are ready — Plan 02 can wire them into the interactive catalog page
- Backend `image_url` field now available for card image rendering
- Plan 02 will create `frontend/app/catalog/page.tsx` (Server Component) and `catalog-client.tsx` (Client Component) to compose these pieces with filter state and URL synchronization

---
*Phase: 14-web-catalog-page*
*Completed: 2026-03-21*
