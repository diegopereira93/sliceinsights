# Codebase Structure

**Analysis Date:** 2026-03-19

## Directory Layout

```
sliceinsights/
├── app/                           # Backend FastAPI application
│   ├── main.py                    # FastAPI app entry point, middleware setup
│   ├── config.py                  # Settings and environment variable loading
│   ├── api/                       # HTTP endpoint handlers
│   │   ├── routes.py              # Main router with /health, /brands, /paddles, /recommendations, /search, /chat, /leads
│   │   └── endpoints/
│   │       ├── alerts.py          # Price alert endpoints
│   │       └── history.py         # Paddle view history endpoints
│   ├── db/                        # Database layer
│   │   ├── database.py            # AsyncEngine, AsyncSession, init_db()
│   │   └── seed_brazil_catalog.py # Hybrid seed logic for Brazilian + international paddles
│   ├── models/                    # Domain models (SQLModel tables)
│   │   ├── paddle.py              # PaddleMaster, PaddleRead (response), PaddleRatings
│   │   ├── brand.py               # Brand entity
│   │   ├── market_offer.py        # MarketOffer for store price listings
│   │   ├── lead.py                # Lead for quiz gate email capture
│   │   ├── price_alert.py         # PriceAlert subscription model
│   │   ├── price_snapshot.py      # Historical price tracking
│   │   ├── ai_knowledge.py        # AI knowledge base entries
│   │   ├── enums.py               # PlayStyle, FaceMaterial, PaddleShape enums
│   │   └── __init__.py            # Model exports
│   ├── schemas/                   # Request/response validation (Pydantic)
│   │   ├── user_profile.py        # RecommendationRequest, UserProfile, RecommendationResult
│   │   └── chat.py                # ChatMessage, ChatRequest, ChatResponse
│   └── services/                  # Business logic layer
│       ├── recommendation_engine.py # RecommendationEngine with AI ranking
│       ├── llm_service.py         # LLMService for Groq API calls
│       ├── affiliate_service.py   # URL transformation for store links
│       ├── price_alerts.py        # Price alert logic
│       ├── enrichment.py          # Paddle spec enrichment
│       └── __init__.py            # Service exports
├── frontend/                      # Next.js frontend application
│   ├── app/                       # Next.js App Router pages
│   │   ├── page.tsx               # Home page (quiz + catalog view)
│   │   ├── statistics/page.tsx    # Market intelligence page
│   │   ├── offline/page.tsx       # PWA offline fallback
│   │   ├── layout.tsx             # Root layout (metadata, fonts, providers)
│   │   ├── error.tsx              # Error boundary for errors
│   │   ├── global-error.tsx       # Global error handler
│   │   └── not-found.tsx          # 404 page
│   ├── components/                # Reusable React components
│   │   ├── ui/                    # Shadcn/ui + custom components
│   │   │   ├── card.tsx           # Card wrapper
│   │   │   ├── badge.tsx          # Badge labels
│   │   │   ├── button.tsx         # Button (variant system)
│   │   │   ├── dialog.tsx         # Modal dialog
│   │   │   ├── drawer.tsx         # Side drawer
│   │   │   ├── tabs.tsx           # Tab switcher
│   │   │   ├── slider.tsx         # Range input
│   │   │   ├── select.tsx         # Dropdown select
│   │   │   ├── tooltip.tsx        # Hover tooltips
│   │   │   ├── spec-item.tsx      # Paddle spec display
│   │   │   ├── performance-bar.tsx # Rating bars (power, control, spin)
│   │   │   ├── radar-chart.tsx    # Specs radar visualization
│   │   │   ├── weight-sensation-scale.tsx # Weight UX slider
│   │   │   ├── price-sparkline.tsx # Mini price history chart
│   │   │   ├── circular-progress.tsx # Match percentage display
│   │   │   ├── error-boundary.tsx # React error catching
│   │   │   ├── empty-state.tsx    # No results message
│   │   │   └── toaster.tsx        # Toast notifications
│   │   ├── paddle/                # Paddle-specific components
│   │   │   ├── paddle-card.tsx    # Catalog card with price, specs
│   │   │   ├── paddle-detail-drawer.tsx # Full paddle details modal
│   │   │   ├── paddle-comparator.tsx # Side-by-side comparison
│   │   │   ├── racket-finder-quiz.tsx # 10-question recommendation quiz
│   │   │   ├── coach-chat-interface.tsx # LLM chat for paddle advice
│   │   │   ├── filter-drawer.tsx  # Paddle filter UI
│   │   │   └── price-alert-dialog.tsx # Subscribe to price drop alerts
│   │   ├── statistics/            # Market intelligence components
│   │   │   ├── distribution-chart.tsx # Price distribution histograms
│   │   │   ├── market-segments.tsx # Segmentation by spec ranges
│   │   │   ├── hidden-gems.tsx    # Best value recommendations
│   │   │   ├── leaderboard-card.tsx # Top paddles by metric
│   │   │   ├── brand-intelligence.tsx # Brand insights
│   │   │   ├── scatter-filters.tsx # Spec scatter plot filters
│   │   │   └── technical-specs-charts.tsx # Detailed spec charts
│   │   ├── layout/                # Page layout components
│   │   │   └── mobile-layout.tsx  # Mobile wrapper with bottom nav
│   │   ├── home-client.tsx        # Home page client component
│   │   ├── statistics-client.tsx  # Statistics page client component
│   │   ├── import-calculator/     # Import duty calculator
│   │   │   └── import-calculator.tsx
│   │   └── (others)
│   ├── lib/                       # Utilities and helpers
│   │   ├── api.ts                 # API client functions (getApiBaseUrl, chatWithCoach, etc.)
│   │   ├── utils.ts               # Class name merging, formatting
│   │   └── import-utils.ts        # Import calculation logic
│   ├── public/                    # Static assets
│   │   ├── images/                # Brand logos, icons
│   │   ├── manifest.json          # PWA manifest
│   │   └── og-image.jpg           # Open Graph image
│   ├── globals.css                # Tailwind + global styles
│   ├── tailwind.config.js         # Tailwind theme customization (Lime Green #CEFF00)
│   ├── next.config.js             # Next.js config
│   ├── tsconfig.json              # TypeScript compiler options
│   ├── package.json               # Frontend dependencies
│   ├── vercel.json                # Vercel deployment config
│   ├── e2e/                       # End-to-end tests (Playwright)
│   └── playwright.config.ts       # Playwright E2E test config
├── scripts/                       # Utility scripts
│   ├── scrape_brazil_store.py    # Web scraper for Brazil Pickleball Store
│   ├── scrape_mercado_livre.py   # Mercado Livre scraper (partial)
│   └── verify.sh                 # Lint, test, security verification script
├── data/                          # Data files (CSV, exports)
│   └── raw/
│       ├── brazil_pickleball_store.csv # Scraped Brazilian paddle data
│       ├── paddle_stats_dump.csv # International specs database
│       └── joola_brazil.csv      # Joola brand specific data
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md            # Existing architecture doc
│   ├── DEPLOYMENT.md              # Deployment guide
│   ├── features/                  # Feature documentation
│   ├── technical/                 # Technical specs
│   └── operations/                # Operational guides
├── alembic/                       # Database migrations
│   ├── env.py                     # Alembic environment config
│   ├── script.py.mako             # Migration template
│   ├── versions/                  # Migration files
│   └── alembic.ini                # Alembic config
├── tests/                         # Backend tests
│   └── (test files for API endpoints and services)
├── .github/                       # GitHub Actions
│   └── workflows/
│       ├── production-pipeline.yml # CI/CD for main branch
│       └── (other workflows)
├── docker-compose.yml             # Local development stack (frontend, backend, postgres)
├── docker-compose.prod.yml        # Production stack configuration
├── Dockerfile                     # Backend container image
├── Dockerfile.frontend            # Frontend container image
├── Makefile                       # Common commands
├── README.md                      # Project overview
├── requirements.txt               # Backend dependencies (FastAPI, SQLModel, etc.)
├── requirements-dev.txt           # Dev dependencies (pytest, black, etc.)
└── alembic.ini                    # Alembic migrations configuration
```

## Directory Purposes

**`app/`:**
- Purpose: FastAPI backend application code
- Contains: API routes, database models, business logic, configuration
- Key files: `main.py` (startup), `config.py` (env vars), `api/routes.py` (endpoints)

**`app/models/`:**
- Purpose: SQLModel ORM entities (database tables) and Pydantic response schemas
- Contains: PaddleMaster, Brand, MarketOffer, Lead, PriceAlert, enums
- Key files: `paddle.py` (core domain entity), `enums.py` (PlayStyle, FaceMaterial, PaddleShape)

**`app/services/`:**
- Purpose: Business logic abstraction from routes
- Contains: RecommendationEngine, LLMService, AffiliateService, PriceAlerts, Enrichment
- Key files: `recommendation_engine.py` (main matching logic), `llm_service.py` (Groq integration)

**`app/db/`:**
- Purpose: Database connection, session management, migrations
- Contains: AsyncEngine setup, session factory, initialization, schema sync
- Key files: `database.py` (session management), `seed_brazil_catalog.py` (data loading)

**`app/api/`:**
- Purpose: HTTP request handlers with dependency injection
- Contains: Route definitions, request/response mapping, rate limiting
- Key files: `routes.py` (main endpoints), `endpoints/` (modular route groups)

**`frontend/app/`:**
- Purpose: Next.js App Router page components and layouts
- Contains: Page routes, root layout, error handlers
- Key files: `page.tsx` (home), `layout.tsx` (root), `statistics/page.tsx` (intelligence)

**`frontend/components/`:**
- Purpose: Reusable React components organized by domain
- Contains: UI primitives, paddle-specific features, market intelligence visualizations
- Key files: `paddle/racket-finder-quiz.tsx` (quiz), `paddle/paddle-detail-drawer.tsx` (details), `statistics/` (charts)

**`frontend/lib/`:**
- Purpose: Utilities, helpers, API client
- Contains: API functions, type definitions, formatting helpers
- Key files: `api.ts` (fetch wrappers, type defs), `utils.ts` (class merging)

**`alembic/`:**
- Purpose: Database schema versioning and migrations
- Contains: Migration scripts, environment configuration
- Key files: `versions/` (auto-generated migration files), `env.py` (Alembic setup)

**`data/raw/`:**
- Purpose: Source data from scrapers
- Contains: CSV exports of paddle specs and pricing
- Key files: `brazil_pickleball_store.csv`, `paddle_stats_dump.csv`

## Key File Locations

**Entry Points:**
- `app/main.py`: FastAPI app startup with middleware and lifespan handlers
- `frontend/app/page.tsx`: Home page component
- `frontend/app/layout.tsx`: Root layout with metadata and providers

**Configuration:**
- `app/config.py`: Environment variable loading and validation via Pydantic Settings
- `frontend/tailwind.config.js`: Theme customization (Lime Green #CEFF00)
- `docker-compose.yml`: Local development services
- `alembic.ini`: Migration runner configuration

**Core Logic:**
- `app/api/routes.py`: All main API endpoints (brands, paddles, recommendations, search, chat)
- `app/services/recommendation_engine.py`: Paddle matching with AI augmentation
- `app/services/llm_service.py`: Groq API wrapper for LLM calls
- `frontend/components/paddle/racket-finder-quiz.tsx`: 10-question quiz component

**Testing:**
- `tests/`: Backend pytest test files
- `frontend/e2e/`: Playwright E2E tests
- `.github/workflows/production-pipeline.yml`: CI/CD pipeline definition

## Naming Conventions

**Files:**
- Python: snake_case for modules and files (`recommendation_engine.py`, `paddle.py`)
- TypeScript: camelCase for exports, PascalCase for components (`racketFinderQuiz.tsx`, `PaddleCard.tsx`)
- Routes: kebab-case for page segments (`app/statistics/page.tsx`)

**Directories:**
- Feature directories: lowercase plural (`models/`, `services/`, `endpoints/`)
- Component domains: descriptive lowercase (`ui/`, `paddle/`, `statistics/`, `layout/`)

**Database tables:**
- snake_case with singular names (`paddle_master`, `market_offer`, `price_alert`)

**Classes/Types:**
- PascalCase: `PaddleMaster`, `RecommendationEngine`, `UserProfile`, `ChatRequest`
- Enums: PascalCase (`PlayStyle`, `FaceMaterial`, `PaddleShape`)

**Functions:**
- Python: snake_case (`get_recommendations`, `calculate_paddle_ratings`)
- TypeScript: camelCase (`getApiBaseUrl`, `chatWithCoach`)

## Where to Add New Code

**New Feature (Quiz alternative or new page):**
- Primary code: `frontend/app/[feature]/page.tsx` + `frontend/components/[feature]/`
- Tests: `frontend/e2e/[feature].spec.ts`
- API (if needed): `app/api/endpoints/[feature].py`

**New Component/Module:**
- UI primitive: `frontend/components/ui/[name].tsx`
- Feature component: `frontend/components/[domain]/[name].tsx`
- Backend service: `app/services/[name].py`

**Utilities:**
- Frontend helpers: `frontend/lib/[purpose].ts`
- Backend helpers: `app/services/` (as utility classes or functions within services)
- Shared types: `frontend/lib/api.ts` (BackendPaddle, RecommendationRequest, etc.)

**Data Models:**
- New database table: `app/models/[entity].py`
- New response schema: `app/schemas/[purpose].py` or add to `app/models/paddle.py`

**API Endpoint:**
- New route: Add to `app/api/routes.py` as `@router.get()` or `@router.post()`
- Modular route group: New file in `app/api/endpoints/[group].py`, include in `routes.py` via `router.include_router()`

## Special Directories

**`frontend/.next/`:**
- Purpose: Next.js build cache and compiled output
- Generated: Yes
- Committed: No (in .gitignore)

**`frontend/node_modules/`:**
- Purpose: npm installed dependencies
- Generated: Yes (via npm install)
- Committed: No (in .gitignore)

**`data/raw/`:**
- Purpose: Source CSV files from scrapers
- Generated: Yes (by scraper scripts)
- Committed: No (in .gitignore)

**`alembic/versions/`:**
- Purpose: Auto-generated database migration scripts
- Generated: Yes (by `alembic revision --autogenerate`)
- Committed: Yes (required for reproducible deployments)

**`.planning/`:**
- Purpose: GSD planning documents and analysis
- Generated: Yes (by GSD agents)
- Committed: Yes

---

*Structure analysis: 2026-03-19*
