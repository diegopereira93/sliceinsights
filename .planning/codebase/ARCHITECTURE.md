# Architecture

**Analysis Date:** 2026-03-19

## Pattern Overview

**Overall:** Clean Architecture with Service Layer pattern (Backend) + Next.js App Router (Frontend)

**Key Characteristics:**
- Monorepo structure with independent frontend (Next.js) and backend (FastAPI) deployments
- Async-first Python backend with SQLModel ORM and PostgreSQL
- Server-side rendered frontend with client components for interactivity
- Request-response API design with REST endpoints
- Recommendation engine with optional AI ranking layer
- Production-hardened with observability, rate limiting, and security middleware

## Layers

**API Layer:**
- Purpose: HTTP endpoint handlers and request routing
- Location: `app/api/routes.py`, `app/api/endpoints/alerts.py`, `app/api/endpoints/history.py`
- Contains: Route handlers with dependency injection, FastAPI decorators, request/response models
- Depends on: Database session, services, schemas
- Used by: Frontend client, external API consumers

**Service Layer:**
- Purpose: Business logic abstraction for recommendations, enrichment, affiliate management, price alerts
- Location: `app/services/` directory
- Contains: `recommendation_engine.py` (user profile matching), `llm_service.py` (Groq LLM calls), `affiliate_service.py` (URL transformation), `price_alerts.py`, `enrichment.py`
- Depends on: Models, database queries, external APIs (LLM)
- Used by: Routes, other services

**Data Access Layer:**
- Purpose: Database connection, session management, schema creation, migrations
- Location: `app/db/database.py`, `alembic/` (migrations)
- Contains: AsyncEngine, session factory, initialization logic, missing column sync
- Depends on: SQLModel, PostgreSQL
- Used by: All services and routes via dependency injection

**Domain Model Layer:**
- Purpose: Data structures and validation rules for domain entities
- Location: `app/models/` directory
- Contains: `PaddleMaster`, `Brand`, `MarketOffer`, `PriceSnapshot`, `Lead`, `PriceAlert`, enum definitions
- Depends on: SQLModel, Pydantic validators
- Used by: Database queries, API responses, business logic

**Schema Layer:**
- Purpose: Request/response validation and transformation
- Location: `app/schemas/` directory
- Contains: `user_profile.py` (RecommendationRequest, UserProfile), `chat.py` (ChatRequest, ChatResponse), custom validators
- Depends on: Pydantic, models
- Used by: API endpoints for request parsing and response serialization

## Data Flow

**Recommendation Quiz Flow:**

1. Frontend (`components/paddle/racket-finder-quiz.tsx`) collects user inputs (skill level, budget, play style, tennis elbow)
2. POST `/api/v1/recommendations` with `RecommendationRequest` schema
3. Route handler creates `UserProfile` object with preferences
4. `RecommendationEngine.get_recommendations()` executes in-service:
   - Subquery aggregates active `MarketOffer` prices and counts for each paddle
   - Hard filters applied (tennis elbow → core_thickness_mm >= 16mm)
   - Budget filter applied via min_price from offers
   - Candidate pool randomized for diversity (20 paddles if AI ranking enabled)
   - Optional: AI ranking via `llm_service.rank_paddles()` (Groq LLM enrichment)
5. Results mapped to `RecommendationResult` schema with match reasons and value scores
6. Frontend renders recommendations with affiliate-transformed URLs

**Paddle Detail & Chat Flow:**

1. Frontend requests `/api/v1/paddles/{paddle_id}` with single query including eager-loaded brand and market offers
2. Affiliate service transforms all offer URLs based on store type
3. Frontend opens `coach-chat-interface.tsx`, sends chat messages with paddle context
4. POST `/api/v1/chat` includes paddle specs and available offers in context
5. `llm_service.chat_with_context()` calls Groq API with enriched technical specifications
6. LLM responds aware of exact specs, available offers, and prices in BRL

**State Management:**
- Backend: In-memory TTL caches for brands (5 min) and paddles (1 min) via `cachetools.TTLCache`
- Frontend: React component state via hooks, no global state manager (no Redux/Zustand)
- Database: Single source of truth for all persistent data via PostgreSQL

## Key Abstractions

**RecommendationEngine:**
- Purpose: Encapsulates complex paddle matching logic with caching and AI augmentation
- Examples: `app/services/recommendation_engine.py`
- Pattern: Class-based service with async methods, dependency injected AsyncSession, optional AI fallback

**LLMService:**
- Purpose: Abstracts external LLM calls (Groq) for ranking and chat
- Examples: `app/services/llm_service.py`
- Pattern: Singleton-like service instance, context-aware prompts, error handling

**AffiliateService:**
- Purpose: Transforms store URLs to affiliate links based on store configuration
- Examples: `app/services/affiliate_service.py`
- Pattern: URL pattern matching and transformation, configurable via env vars

**PaddleRead Response Schema:**
- Purpose: Unified data format for frontend paddle display
- Examples: `app/models/paddle.py` (PaddleRead class)
- Pattern: Pydantic model with custom `from_paddle()` factory method, includes brand, specs, ratings, min_price

## Entry Points

**Backend:**
- Location: `app/main.py`
- Triggers: `uvicorn app.main:app` or Docker container startup
- Responsibilities: FastAPI app initialization, middleware setup (CORS, security headers, rate limiting, compression), structlog configuration, Sentry integration, Prometheus instrumentation, database initialization

**Frontend:**
- Location: `frontend/app/page.tsx` (home), `frontend/app/layout.tsx` (root)
- Triggers: Next.js development server (`npm run dev`) or production build
- Responsibilities: Root layout with metadata, fonts, toaster setup, page routing via App Router

**Database Migration:**
- Location: `alembic/` directory
- Triggers: `alembic upgrade head` or automatic init_db() on app startup
- Responsibilities: Schema versioning, column additions via Alembic ORM, sync column detection for existing tables

## Error Handling

**Strategy:** Try-catch with structured logging and HTTP exception responses

**Patterns:**
- Routes wrap queries in try-except, raise `HTTPException(status_code=...)` for client errors (404, 403, 400)
- Database errors (connection, constraint violations) logged with full traceback, return 500 with sanitized message
- Health check endpoint returns 503 if database disconnected
- Frontend error boundaries (`components/ui/error-boundary.tsx`) catch React component errors and show fallback UI
- LLM service includes timeout and fallback logic for Groq API failures

## Cross-Cutting Concerns

**Logging:** Structlog with JSON output in production (via `configure_logging()` in main.py), console output in debug mode. All requests logged with method, path, status_code, process_time_ms. Services use `logger = structlog.get_logger(__name__)` for context-aware logs.

**Validation:** Pydantic models enforce schema validation on all inputs (RecommendationRequest, ChatRequest, LeadCreate). SQLModel fields include validators for ratings (0-10 range), twist_weight (non-negative). Search endpoints validate query string length (min 2 chars).

**Authentication:** No user authentication currently. Admin endpoints (seed, diag) protected by `ADMIN_SEED_SECRET` environment variable passed as query parameter. Frontend publicly accessible.

**Rate Limiting:** Slowapi middleware with per-endpoint limits:
- `/health` - unrestricted
- `/paddles` - 100/minute
- `/recommendations` - 30/minute
- `/search` - 60/minute
- `/chat` - 20/minute
- `/leads` - 10/minute
- Default: 30/minute for undecorated endpoints

**Security:** Security headers set via middleware (CSP, HSTS, X-Frame-Options, X-Content-Type-Options). CORS whitelist includes localhost, Vercel preview URLs, and production domain. GZip compression enabled for responses > 500 bytes.

---

*Architecture analysis: 2026-03-19*
