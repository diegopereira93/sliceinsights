# SliceInsights - Insights precisos para sua melhor jogada

🏓 Uma plataforma premium de recomendação de raquetes de Pickleball, focada em alta performance, UX sofisticada e conversão.

## ✨ Features

- **Racket Finder Quiz v3**: Consultor dinâmico com **Labor Illusion** (mensagens de processamento em tempo real) para feedback imersivo.
- **Cromatismo Técnico**: Atributos técnicos (Power, Control, Spin, Sweet Spot) codificados por cores para escaneamento visual rápido.
- **Design System Premium**: Interface moderna com cores vibrantes (Lime Green #CEFF00), Glassmorphism e Dark Mode nativo.
- **SE Refactor (High Performance)**: Backend otimizado com SQL Joins (resolvendo N+1 queries) e filtros de banco de dados para escalabilidade.
- **Mobile-First PWA**: Experiência de app nativo focada em dispositivos móveis.

## 🛡️ Production-Ready Features

- **Rate Limiting**: Proteção contra abuso de API (30-100 req/min por endpoint)
- **CORS Whitelist**: Segurança configurável para origens permitidas
- **Prometheus Metrics**: Métricas de performance em `/metrics`
- **Structured Logging**: Logs JSON com structlog
- **Sentry Integration**: Error tracking (configurável via `SENTRY_DSN`)
- **Health Check**: Validação de conexão com DB em `/api/v1/health`
- **Error Boundaries**: Tratamento gracioso de erros no frontend
- **CI/CD Pipeline**: GitHub Actions para testes e build

## 🛠️ Tech Stack

- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + Framer Motion
- **UI Components**: Shadcn/ui + Lucide Icons + Radix UI
- **Backend**: FastAPI + SQLModel + AsyncPG
- **Database**: PostgreSQL 16
- **Testing**: Pytest (backend) + Playwright (E2E)
- **Observability**: Prometheus + Sentry + Structlog
- **Architecture**: Clean Architecture / Service Layer Pattern

## 🚀 Quick Start (Docker)

```bash
# Iniciar todos os serviços (Desenvolvimento)
docker compose up -d --build

# Acessar:
# - Frontend: http://localhost:3000
# - API Backend: http://localhost:8002
# - Swagger Docs: http://localhost:8002/docs
# - Prometheus Metrics: http://localhost:8002/metrics
```

## 🏭 Production Deploy

### Opção 1: Railway (Gratuito) ⭐

Deploy full-stack grátis em [railway.app](https://railway.app):

```bash
# 1. Conecte seu repositório GitHub no Railway
# 2. Adicione PostgreSQL database
# 3. Configure variáveis de ambiente
# 4. Deploy automático!
```

📚 Guia completo: [docs/railway_deploy.md](docs/railway_deploy.md)

### Opção 2: Docker (Self-hosted)

```bash
# Build e deploy de produção
docker compose -f docker-compose.prod.yml up -d --build
```

## 🧪 Testes

```bash
# Backend tests
docker compose exec backend_v3 pytest tests/ -v

# Frontend E2E (requer Playwright instalado)
cd frontend && npx playwright test
```

## 📂 Project Structure

```
niteroi-raquetes/
├── app/                      # FastAPI Backend
│   ├── api/routes.py         # API endpoints com rate limiting
│   ├── config.py             # Configurações (CORS, logging, etc)
│   ├── main.py               # App entry com Sentry/Prometheus
│   └── services/             # Recommendation engine
├── frontend/                 # Next.js Frontend
│   ├── app/                  # Routes, error boundaries
│   ├── components/           # UI components
│   └── e2e/                  # Playwright E2E tests
├── tests/                    # Backend tests
├── .github/workflows/        # CI/CD pipelines
├── docker-compose.yml        # Dev environment
├── docker-compose.prod.yml   # Production environment
└── docs/                     # Documentation
```

## ⚙️ Environment Variables

Copie `.env.example` para `.env` e configure:

| Variable | Description | Required |
|----------|-------------|----------|
| `POSTGRES_PASSWORD` | Database password | ✅ |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | ✅ |
| `SENTRY_DSN` | Sentry error tracking | ❌ |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, etc) | ❌ |

## 📚 Documentation

- [Production Readiness Roadmap](docs/production_readiness_roadmap.md) ✅ **Implemented**
- [API Specification](docs/api_specification.md)
- [Database Schema](docs/database_schema.md)
- [Runbook](docs/runbook.md)

## 📄 License

MIT
