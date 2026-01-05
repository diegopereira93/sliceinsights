# Production Readiness Roadmap - Niterói Raquetes

Roadmap técnico para tornar o projeto production-ready. Organizado por prioridade e esforço.

---

## 🔴 Fase 0 - Bloqueadores de Deploy (~8h)

### 0.1 Segurança - CORS

| Arquivo | Mudança |
|---------|---------|
| `app/main.py` | Substituir `allow_origins=["*"]` por lista whitelist |
| `app/config.py` | Adicionar `allowed_origins: list[str]` com default para dev |

**Implementação:**
```python
# app/config.py
allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8002"]

# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

---

### 0.2 Segurança - Credenciais

| Arquivo | Mudança |
|---------|---------|
| `docker-compose.yml` | Usar variáveis de ambiente sem defaults |
| `app/config.py` | Remover defaults de credentials |
| `.env.example` | Documentar variáveis obrigatórias |

**Regra:** Nenhuma senha real em código versionado.

---

### 0.3 CI/CD Pipeline

**Criar:** `.github/workflows/ci.yml`

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v --tb=short

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install & Build
        working-directory: ./frontend
        run: |
          npm ci
          npm run build

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python lint
        run: pip install ruff && ruff check app/
      - name: Frontend lint
        working-directory: ./frontend
        run: npm ci && npm run lint
```

---

### 0.4 Health Check Real

| Arquivo | Mudança |
|---------|---------|
| `app/api/routes.py` | Health check deve validar conexão com DB |

```python
@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    try:
        await session.exec(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
```

---

## 🟠 Fase 1 - Robustez (~10h)

### 1.1 Rate Limiting

| Arquivo | Mudança |
|---------|---------|
| `requirements.txt` | Adicionar `slowapi>=0.1.9` |
| `app/main.py` | Configurar limiter global |
| `app/api/routes.py` | Decorar endpoints críticos |

**Limites sugeridos:**
- `/recommendations`: 30 req/min
- `/search`: 60 req/min
- `/paddles`: 100 req/min

---

### 1.2 Logging Estruturado

| Arquivo | Mudança |
|---------|---------|
| `requirements.txt` | Adicionar `structlog>=24.0.0` |
| `app/config.py` | Adicionar `log_level: str = "INFO"` |
| `app/main.py` | Configurar structlog |
| `app/api/routes.py` | Logar requests importantes |

---

### 1.3 Frontend Error Boundary

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/error.tsx` | **[NOVO]** Global error boundary |
| `frontend/app/global-error.tsx` | **[NOVO]** Root layout error |
| `frontend/app/not-found.tsx` | **[NOVO]** 404 page customizada |

---

### 1.4 Testes de API

| Arquivo | Mudança |
|---------|---------|
| `tests/test_api_paddles.py` | **[NOVO]** Testes CRUD paddles |
| `tests/test_api_recommendations.py` | **[NOVO]** Testes do engine |
| `tests/conftest.py` | **[NOVO]** Fixtures compartilhadas |

**Cobertura alvo:** 60%+

---

## 🟡 Fase 2 - Performance (~8h)

### 2.1 Otimizar N+1 Queries

| Arquivo | Mudança |
|---------|---------|
| `app/api/routes.py` | Refatorar `list_paddles` com subquery |

**De:**
```python
for paddle in paddles:
    min_price_result = await session.exec(...)  # N queries
```

**Para:**
```python
# Uma única query com agregação
subq = select(
    MarketOffer.paddle_id,
    func.min(MarketOffer.price_brl).label("min_price"),
    func.count().label("count")
).group_by(MarketOffer.paddle_id).subquery()

query = select(PaddleMaster, subq).outerjoin(subq)
```

---

### 2.2 Docker Production Build

| Arquivo | Mudança |
|---------|---------|
| `Dockerfile.frontend` | Multi-stage build |
| `docker-compose.prod.yml` | **[NOVO]** Config de produção |

**Dockerfile.frontend (multi-stage):**
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
CMD ["node", "server.js"]
```

---

### 2.3 Caching de Respostas

| Arquivo | Mudança |
|---------|---------|
| `app/services/recommendation_engine.py` | TTL cache para resultados |
| `next.config.mjs` | Cache headers para assets |

---

## 🔵 Fase 3 - Observabilidade (~8h)

### 3.1 Error Tracking (Sentry)

| Arquivo | Mudança |
|---------|---------|
| `requirements.txt` | Adicionar `sentry-sdk[fastapi]` |
| `app/main.py` | Inicializar Sentry |
| `frontend/package.json` | Adicionar `@sentry/nextjs` |

---

### 3.2 Métricas (Prometheus)

| Arquivo | Mudança |
|---------|---------|
| `requirements.txt` | Adicionar `prometheus-fastapi-instrumentator` |
| `app/main.py` | Expor `/metrics` |

---

### 3.3 Testes E2E (Playwright)

| Arquivo | Mudança |
|---------|---------|
| `frontend/package.json` | Adicionar `@playwright/test` |
| `frontend/e2e/quiz.spec.ts` | **[NOVO]** Teste do flow principal |
| `.github/workflows/e2e.yml` | **[NOVO]** Pipeline E2E |

---

## ✅ Checklist de Validação

### Antes do Deploy
- [x] CORS restrito a domínios específicos
- [x] Nenhuma credencial em código
- [x] CI passa em todos os jobs
- [x] Health check valida DB

### Primeira Release
- [x] Rate limiting ativo
- [x] Logs estruturados funcionando
- [x] Error boundaries no frontend
- [x] Cobertura de testes > 50%

### Maturidade
- [x] Sentry capturando erros
- [x] Dashboards de métricas
- [x] Testes E2E no CI
- [x] Docker multi-stage em prod

> **Status: ✅ IMPLEMENTADO** (Janeiro 2026)

---

## 📊 Estimativa Total

| Fase | Esforço | Prioridade |
|------|---------|------------|
| Fase 0 | ~8h | P0 - Bloqueador |
| Fase 1 | ~10h | P1 - Essencial |
| Fase 2 | ~8h | P2 - Performance |
| Fase 3 | ~8h | P3 - Observabilidade |
| **Total** | **~34h** | |
