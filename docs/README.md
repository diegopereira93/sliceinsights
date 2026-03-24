# SliceInsights — Catálogo Confiável Brasileiro

> Plataforma de recomendação de raquetes de Pickleball com IA e catálogo confiável, focada no mercado brasileiro.

**Milestone:** v3 | **Status:** Em desenvolvimento (Phase 17)

---

## Quick Start

```bash
# 1. Subir serviços
docker compose up -d --build

# 2. Acessar
#   Frontend Vite:  http://localhost:5173
#   API FastAPI:    http://localhost:8002

# 3. Seed dev catalog (primeira vez)
docker compose run seed_v3
```

---

## Arquitetura

```
frontend-vite/     → Vite SPA (React 19, Tailwind 4, React Query)
     ↓ VITE_API_URL
app/               → FastAPI backend (Python)
     ↓ DATABASE_URL
postgres_v3/       → PostgreSQL 16 + pgvector
```

### Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Vite 7, React 19, Tailwind 4, React Query, Framer Motion |
| Backend | FastAPI, SQLModel, asyncpg, Orval |
| Database | PostgreSQL 16 + pgvector |
| Deploy | Docker Compose |

---

## Estrutura

```
sliceinsights/
├── frontend-vite/       # Vite SPA (Phase 17)
│   ├── src/pages/       # Home, Quiz, Chat, Stats
│   ├── src/components/  # UI components
│   └── src/lib/api-client/  # Orval-generated API client
├── app/                 # FastAPI backend
│   ├── api/endpoints/   # Route handlers
│   └── main.py          # Entry point
├── scripts/             # Scraper, seed, deploy scripts
├── data/                # Seed data CSV
├── docs/                # Documentação
│   ├── deploy-guide.md  # Deploy & release
│   └── slo-guide.md     # SLO monitoring
├── tests/               # Testes automatizados
└── docker-compose.yml
```

---

## API Endpoints

| Route | Description |
|-------|-------------|
| `GET /api/healthz` | Health check |
| `GET /api/paddles` | List paddles (paginated, filterable) |
| `GET /api/paddles/{id}` | Paddle by ID |
| `POST /api/quiz/recommend` | AI recommendation |
| `POST /api/leads` | Lead capture |
| `POST /api/chat` | Chat endpoint |
| `GET /api/stats/market` | Market statistics |
| `GET /api/stats/brands` | Brand stats |
| `GET /api/stats/hidden-gems` | Hidden gems |

Swagger: http://localhost:8002/docs

---

## Scripts Úteis

```bash
# Database
docker compose up postgres_v3 -d

# Backend com hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend-vite && npm install && npm run dev

# Seed dev catalog
docker compose run seed_v3

# Deploy data pipeline
python scripts/deploy_worker.py --run
```

---

## Testes

```bash
pytest tests/ -v
```

---

## Roadmap

Progresso atual: `.planning/ROADMAP.md`

| Phase | Status |
|-------|--------|
| 11-16 | ✅ Complete |
| 17 — UI Redesign (Vite SPA) | 🔄 In Progress |
| 18 | 📋 Planned |

---

## Links

- **Swagger API:** http://localhost:8002/docs
- **Progress:** `.planning/ROADMAP.md`

---

*Última Atualização: Marzo 2026 | Milestone: v3.0*
