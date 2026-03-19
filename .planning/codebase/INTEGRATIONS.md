# External Integrations

**Analysis Date:** 2026-03-19

## APIs & External Services

**LLM (Large Language Model):**
- Groq API - LLM inference for paddle recommendations and chat
  - SDK/Client: groq==0.13.0
  - Auth: GROQ_API_KEY (environment variable)
  - Model: llama-3.3-70b-versatile
  - Usage: `app/services/llm_service.py` - generate_dossier(), generate_ai_recommendations(), chat_with_context()

**E-commerce & Affiliate:**
- Amazon Associates - Affiliate monetization for product links
  - Auth: AFFILIATE_AMAZON_TAG (environment variable)
  - Transformation: `app/services/affiliate_service.py` - adds ?tag= parameter to Amazon URLs
  - Example: amazon.com.br product links converted to affiliate links

- Mercado Livre - Brazilian marketplace affiliate program
  - Auth: AFFILIATE_ML_ID (environment variable)
  - Transformation: `app/services/affiliate_service.py` - adds ?aff_id= parameter
  - Supports both mercadolivre and mercadolibre domains

**Notifications:**
- Telegram Bot API - Push notifications for price alerts
  - Auth: TELEGRAM_BOT_TOKEN (environment variable)
  - Chat ID: TELEGRAM_CHAT_ID (environment variable)
  - Endpoint: https://api.telegram.org/bot{token}/sendMessage
  - Usage: `app/services/price_alerts.py` - _send_telegram()
  - Message format: Markdown with emoji formatting

- Generic Webhook - Custom notification endpoint for price alerts
  - Auth: PRICE_ALERT_WEBHOOK_URL (environment variable)
  - Payload: JSON array of price alert objects
  - Usage: `app/services/price_alerts.py` - _send_webhook()
  - Typical use: Discord/Slack webhooks

## Data Storage

**Databases:**
- PostgreSQL 16 (with pgvector extension)
  - Connection: postgresql+asyncpg://... (async) and postgresql://... (sync)
  - Environment: DB_HOST, DB_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
  - Client: SQLModel (ORM based on SQLAlchemy)
  - Vector search: pgvector extension for embeddings
  - Migrations: Alembic (`alembic/` directory implied)

**File Storage:**
- Local filesystem only
  - Paddle catalog data: `data/` directory
  - Seed data: `data/` directory (loaded via `app/db/seed_brazil_catalog.py`)
  - Upload capability: Not detected

**Caching:**
- cachetools library - In-memory caching for Python functions
- Likely used for: LLM responses, product data (implementation not yet inspected)

## Authentication & Identity

**Auth Provider:**
- None detected - Application appears to be public/unauthenticated
- CORS is configured in `app/main.py` for multiple allowed origins
- Rate limiting via slowapi middleware

## Monitoring & Observability

**Error Tracking:**
- Sentry (optional) - Conditional initialization
  - Configuration: SENTRY_DSN (environment variable, optional)
  - Implementation: `app/main.py` (lines 53-59) - initialized if SENTRY_DSN is set
  - Sample rate: 10% traces, 10% profiling
  - Captures: Exceptions and performance traces

**Logs:**
- Structured JSON logging via structlog
  - Framework: structlog 24.1.0
  - Format: JSON in production, console in development
  - Logger factory: PrintLoggerFactory
  - Output: stdout (captured by Docker/container logs)
  - Configuration: `app/main.py` - configure_logging()

**Metrics:**
- Prometheus - Application metrics
  - Client: prometheus-fastapi-instrumentator 6.1.0
  - Endpoint: `/metrics` (exposed via instrumentator)
  - Metrics: Request latency, counts, response codes

## CI/CD & Deployment

**Hosting:**
- Frontend: Vercel (Next.js native deployment)
  - Domains: sliceinsights.vercel.app, sliceinsights.com.br
  - Environment: NEXT_PUBLIC_API_URL points to backend

- Backend: Docker container deployment (Railway or similar cloud provider implied)
  - Server: Uvicorn ASGI with 6 workers in production
  - Port: 8000 (internal), 8002 (mapped in compose)
  - Healthcheck: Database connectivity

**CI Pipeline:**
- GitHub Actions (detected from `.github/` directory)
- Deployment: Automatic to Vercel (frontend), manual or automated to hosting (backend)

**Docker:**
- Frontend Dockerfile: `Dockerfile.frontend` (multi-stage build with builder target)
- Backend Dockerfile: `Dockerfile` (implied in docker-compose.yml)
- Compose dev: `docker-compose.yml` (development with hot reload)
- Compose prod: `docker-compose.prod.yml` (production with resource limits)

## Environment Configuration

**Required env vars:**

*Database:*
- DATABASE_URL - PostgreSQL connection string (asyncpg driver)
- DATABASE_URL_SYNC - PostgreSQL connection string (psycopg2 driver)
- POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
- DB_HOST, DB_PORT

*Backend:*
- DEBUG - Boolean debug mode (false in production)
- LOG_LEVEL - Logging verbosity (INFO recommended)
- ALLOWED_ORIGINS - CORS origins (comma-separated or JSON array)

*Frontend:*
- NEXT_PUBLIC_API_URL - Backend API endpoint (http://localhost:8002/api/v1 locally)

*LLM:*
- GROQ_API_KEY - Groq API authentication key

*Affiliate:*
- AFFILIATE_AMAZON_TAG - Amazon Associates tracking tag (optional)
- AFFILIATE_ML_ID - Mercado Livre affiliate ID (optional)

*Notifications:*
- TELEGRAM_BOT_TOKEN - Telegram Bot API token (optional)
- TELEGRAM_CHAT_ID - Telegram chat ID for alerts (optional)
- PRICE_ALERT_WEBHOOK_URL - Webhook endpoint for price alerts (optional)

*Observability:*
- SENTRY_DSN - Sentry project DSN for error tracking (optional)

**Secrets location:**
- `.env` file (git-ignored) - Local development
- `.env.example` - Reference file with placeholder values
- Environment variables in container runtime - Production (Docker/Railway)
- GitHub Secrets - CI/CD pipeline (implied)

## Webhooks & Callbacks

**Incoming:**
- Price alert notification endpoints:
  - `app/api/endpoints/alerts.py` - Alert management (implied based on file structure)

**Outgoing:**
- Telegram API - sendMessage endpoint for price alerts
- Generic webhook - Custom endpoint for price alerts (PRICE_ALERT_WEBHOOK_URL)
- Groq API - LLM inference requests

## Rate Limiting & Security

**Rate Limiting:**
- Framework: slowapi
- Implementation: `app/main.py` (lines 49)
- Exception handler: _rate_limit_exceeded_handler
- Key function: IP address (remote address)

**CORS:**
- Allowed origins (from `app/config.py`):
  - http://localhost:3000 (dev)
  - http://localhost:3002 (alternate dev)
  - http://localhost:8002 (API)
  - https://frontend-five-iota-18.vercel.app
  - https://sliceinsights.com.br
  - https://sliceinsights.vercel.app
- Methods: GET, POST, OPTIONS
- Credentials: Enabled

**Compression:**
- GZip middleware for responses >500 bytes

---

*Integration audit: 2026-03-19*
