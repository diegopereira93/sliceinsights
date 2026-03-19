# Technology Stack

**Analysis Date:** 2026-03-19

## Languages

**Primary:**
- TypeScript 5.9.3 - Frontend (React/Next.js)
- Python 3.12 - Backend (FastAPI)

**Secondary:**
- JavaScript/JSX - React components in frontend

## Runtime

**Environment:**
- Node.js - Frontend development and build
- Python 3.12 - Backend execution
- Docker/Docker Compose - Containerization

**Package Manager:**
- npm - Node.js packages (frontend)
- pip - Python packages (backend)
- Lockfile: package-lock.json (frontend), requirements.txt (backend)

## Frameworks

**Frontend:**
- Next.js 14.2.35 - React framework with SSR/SSG, image optimization
- React 18.3.1 - UI component library
- TypeScript - Type safety

**Backend:**
- FastAPI 0.115.0 - Async REST API framework
- Uvicorn 0.27.0 - ASGI server

**Styling:**
- Tailwind CSS 3.4.19 - Utility-first CSS framework
- Radix UI - Headless component library
- Class Variance Authority 0.7.1 - Component styling utility
- Framer Motion 11.11.17 - Animation library

**Data Visualization:**
- Recharts 3.6.0 - React charting library

**Database ORM:**
- SQLModel 0.0.14 - SQL database ORM (SQLAlchemy + Pydantic)
- Alembic 1.13.1 - Database migrations

## Key Dependencies

**Critical - Backend:**
- asyncpg 0.29.0 - Async PostgreSQL driver
- psycopg2-binary 2.9.9 - Sync PostgreSQL driver (for migrations/seed)
- pydantic 2.9.2 - Data validation and serialization
- pydantic-settings 2.1.0 - Environment configuration management
- groq 0.13.0 - LLM API client (Groq API)

**Critical - Frontend:**
- @radix-ui/* (multiple versions) - Accessible UI components (dialog, select, slider, tabs, tooltip, toast)
- sharp 0.34.5 - Image processing for Next.js
- lucide-react 0.562.0 - Icon library

**Infrastructure - Backend:**
- slowapi 0.1.9 - Rate limiting middleware
- prometheus-fastapi-instrumentator 6.1.0 - Prometheus metrics
- sentry-sdk 2.8.0 (optional) - Error tracking and monitoring
- structlog 24.1.0 - Structured JSON logging

**Data Processing:**
- pandas 2.2.0 - Data manipulation and analysis
- thefuzz 0.20.0 - String fuzzy matching (for product matching)
- beautifulsoup4 4.12.3 - HTML parsing

**AI & Vector Search:**
- pgvector 0.2.1 - PostgreSQL vector extension for embeddings
- openai 1.14.0 - OpenAI API (available but may not be actively used)

**Utilities:**
- httpx 0.26.0 - Modern HTTP client
- requests 2.31.0 - HTTP library (used for webhooks)
- playwright 1.42.0 - Browser automation (for web scraping)
- python-dotenv 1.0.0 - Environment variable loading
- email-validator 2.1.0 - Email validation
- cachetools 5.3.2 - Caching decorator library
- dlt 0.4.5 - Data loading framework

**Testing - Frontend:**
- @playwright/test 1.40.0 - E2E testing framework
- @types/* (multiple) - TypeScript type definitions
- ESLint 8.57.0 - Linting with Next.js config
- Lighthouse 12.8.2 - Performance auditing

**Build/Dev:**
- autoprefixer 10.4.24 - CSS vendor prefixing
- tailwind-merge 3.4.0 - Merge Tailwind classes
- vaul 1.1.2 - Keyboard utility library
- clsx 2.1.1 - Class name utility
- next-pwa 5.6.0 - Progressive Web App support

## Configuration

**Environment:**
- `.env.example` defines all required variables (see INTEGRATIONS.md)
- Environment variables loaded via pydantic-settings in `app/config.py`
- Frontend env vars prefixed with `NEXT_PUBLIC_` for client-side access

**Build:**
- `tsconfig.json` - TypeScript compiler options (ES2017 target, strict mode)
- `.eslintrc` with Next.js config - Linting rules
- `tailwind.config.js` - Tailwind CSS configuration
- `next.config.js` - Next.js build configuration (implied)

**Frontend Paths:**
- `@/*` maps to frontend root directory for absolute imports

## Database

**PostgreSQL 16:**
- Image: pgvector/pgvector:pg16
- Client library: asyncpg (async), psycopg2 (sync)
- Vector extension enabled for embeddings
- Connection pooling via SQLModel session management

## Platform Requirements

**Development:**
- Node.js (version not explicitly pinned, inferred from package.json)
- Python 3.12 (from .venv directory naming)
- PostgreSQL 16 with pgvector extension
- Docker & Docker Compose

**Production:**
- Docker containers (backend: 512M limit, frontend: 256M limit)
- Vercel (frontend deployment - domains: sliceinsights.vercel.app, sliceinsights.com.br)
- External PostgreSQL database or container service
- Uvicorn ASGI server with 6 workers

**CI/CD:**
- GitHub Actions (implied from .github/ directory)
- Vercel deployment integration

---

*Stack analysis: 2026-03-19*
