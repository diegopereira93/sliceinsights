# Deploy & Release Guide

**Milestone:** v3 — Catálogo Confiável Brasileiro
**Last Updated:** 2026-03-23
**Owner:** Data Engineering

---

## Overview

This guide covers:

- **Data Pipeline:** Nightly batch deployment of scraped racket data (scrapers → PostgreSQL)
- **Backend:** FastAPI API shim running as `backend_v3`
- **Frontend:** Vite SPA at `frontend-vite/` (Phase 17 migration, replacing old Next.js)

**Design principle:** Data pipeline deploys are event-driven. Frontend/backend deploy on code push via Docker.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Nightly Batch Deploy                     │
│                                                          │
│  Scrapers → market_offers_staging                        │
│       ↓                                                  │
│  deploy-nightly.yml (repository_dispatch)               │
│       ↓                                                  │
│  deploy_worker.py --run                                  │
│       ├─ SLO gate check                                  │
│       ├─ Aggregate + validate                            │
│       ├─ Publish to market_offers                        │
│       └─ Prune old versions                             │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│  Production Services (docker-compose)                   │
│                                                          │
│  postgres_v3 (pgvector:pg16)  ← scraped data             │
│       ↑                                                  │
│  backend_v3 (FastAPI + Orval)  ← API shim, Phase 17      │
│       ↑                                                  │
│  frontend_vite (Vite SPA)    ← Phase 17 target            │
└─────────────────────────────────────────────────────────┘
```

### Key Tables

| Table | Role |
|-------|------|
| `market_offers` | Production data served via `/api/paddles`. Tagged with `version_id` + `is_active` |
| `market_offers_staging` | Buffer between scrapers and publish |
| `deploy_logs` | Audit log of every deploy (batch_id, version_id, status, metrics) |
| `slo_logs` | SLO check results for gate validation |

### Version Schema

`market_offers` rows carry two versioning columns:
- `version_id` (INTEGER): sequential version counter per batch deploy
- `is_active` (BOOLEAN): `true` for the live version

Rollback flips `is_active` flags. Zero downtime.

---

## CLI Reference (Data Pipeline)

All commands run from the project root:

```bash
export DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5434/picklematch
```

### `--run` — Full nightly deploy

```bash
python scripts/deploy_worker.py --run [--batch-date YYYY-MM-DD]
```

Runs: SLO gate → aggregate → validate → publish → prune.

**Example output:**
```
[deploy] Starting nightly deploy for batch_20260323_a1b2c
[deploy] SLO gate: 9/11 scrapers passed
[deploy] Aggregating batch batch_20260323_a1b2c (9 scrapers, ~4200 rows)
[deploy] Pre-deploy validation: PASS
[deploy] Publishing batch batch_20260323_a1b2c as version_id=42
[deploy] Deploy complete. 4183 products published.
```

### `--validate-batch` — Re-validate a specific batch

```bash
python scripts/deploy_worker.py --validate-batch BATCH_ID
```

Runs pre-deploy validation without publishing.

### `--force-publish` — Force publish (bypass validation)

```bash
python scripts/deploy_worker.py --force-publish BATCH_ID --operator-id YOUR_NAME
```

Requires `--operator-id` for audit trail.

### `--rollback` — Rollback a deployed batch

```bash
python scripts/deploy_worker.py --rollback BATCH_ID
```

Flips `is_active` flags. Zero downtime.

---

## Rollback Procedure

**Step 1: Identify batch**
```sql
SELECT batch_id, version_id, status, scrapers_passed, products_published, created_at
FROM deploy_logs ORDER BY created_at DESC LIMIT 5;
```

**Step 2: Rollback**
```bash
export DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5434/picklematch
python scripts/deploy_worker.py --rollback batch_20260323_a1b2c
```

**Step 3: Verify**
```sql
SELECT version_id, is_active, COUNT(*) FROM market_offers
GROUP BY version_id, is_active ORDER BY version_id DESC;
```

**Notes:**
- Rollback window: within 24h (after that, N-2 may be pruned)
- Rolled-back version rows are preserved with `is_active = false`

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Deploy aborted: 0 scrapers passed | Fix failing scrapers, check `slo_logs` |
| Validation failed: NULL price_brl/url | Investigate source scraper, fix, re-validate |
| Rollback fails: no previous version | Manual DB recovery. Always rollback within 24h. |
| Deploy timeout (150 min exceeded) | Increase `timeout-minutes` in `deploy-nightly.yml` |
| Webhook not firing | Regenerate `GH_DEPLOY_PAT` with `repo` scope |

---

## Deploy Logs

```sql
-- Last 5 deploys
SELECT batch_id, version_id, status, scrapers_passed, products_published, created_at
FROM deploy_logs ORDER BY created_at DESC LIMIT 5;

-- Failed deploys
SELECT batch_id, version_id, status, abort_reason, created_at
FROM deploy_logs WHERE status IN ('failed', 'aborted') ORDER BY created_at DESC;

-- Active version
SELECT version_id, COUNT(*) as active_products FROM market_offers WHERE is_active = true GROUP BY version_id;
```

---

## Frontend Deployment (Phase 17)

The Vite SPA at `frontend-vite/` replaces the old Next.js frontend.

### Build

```bash
cd frontend-vite
npm install
npm run build
```

Output goes to `frontend-vite/dist/`, served by `frontend-vite/nginx.conf`.

### Environment

```bash
VITE_API_URL=http://localhost:8002   # local
VITE_API_URL=/api                     # production (same origin via nginx)
```

### Docker (when integrated)

The Vite SPA will be served via nginx, replacing the `frontend` service in `docker-compose.yml`.

### GitHub Actions (TBD — Phase 17)

Frontend deploy workflow not yet configured. Planned:

1. Push to `main` triggers `npm run build`
2. Docker image built and pushed to registry
3. `docker-compose` pulled on server

---

## Backend Deployment (FastAPI)

### Local

```bash
docker compose up backend_v3
# or with hot reload:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production

Backend runs as `backend_v3` container in `docker-compose.yml`. On code push:

```bash
docker compose build backend_v3
docker compose up -d backend_v3
```

### API Routes (Phase 17)

| Route | Description |
|-------|-------------|
| `GET /api/healthz` | Health check |
| `GET /api/paddles` | List paddles (new Orval shim) |
| `GET /api/paddles/{id}` | Paddle by sequential ID |
| `POST /api/quiz/recommend` | AI recommendation |
| `POST /api/leads` | Lead capture |
| `POST /api/chat` | Chat endpoint |
| `GET /api/stats/market` | Market statistics |
| `GET /api/stats/brands` | Brand stats |
| `GET /api/stats/hidden-gems` | Hidden gems |

---

## GitHub Actions

### Required Secrets

| Secret | For |
|--------|-----|
| `DATABASE_URL_SYNC` | Deploy job |
| `GH_DEPLOY_PAT` | Scraper CI webhook trigger |
| `TELEGRAM_BOT_TOKEN` | Failure notifications |
| `TELEGRAM_CHAT_ID` | Failure notifications |

### Workflows

- `deploy-nightly.yml` — Data pipeline (triggered by scraper CI)
- `ci.yml` — Lint + tests
- `scrape-enrichment.yml` — Weekly scraper run
- `slo-check.yml` — SLO monitoring

---

*Updated for v3 milestone (Phase 17 — Vite SPA migration) — 2026-03-23*
