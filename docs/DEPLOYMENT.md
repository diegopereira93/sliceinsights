# Deployment Status (v1.8.1)

**Last Updated:** 2026-02-27 (Release v1.8.1 - UX Polish)
**Environment:** Production (Hybrid Pipeline)

## 🏗️ Infrastructure

### Global Pipeline (GitHub Actions)
- **CI**: Backend (Pytest) + Frontend (Next Build)
- **CD**: Auto-trigger on `main` push.
- **Verification**: Playwright E2E Smoke Tests strictly enforced.

### Hosting Matrix
- **Frontend (Vercel)**: Next.js 14 (App Router)
- **Backend (Render)**: FastAPI (Dockerized)
- **Database (Neon)**: Postgres 17 (Serverless)

## 📋 Essential Environment Variables

### Backend (Render)
```bash
DATABASE_URL=***
GROQ_API_KEY=*** # Required for AI Recommendation Engine
ALLOWED_ORIGINS=["https://sliceinsights.vercel.app"]
DEBUG=false
```
