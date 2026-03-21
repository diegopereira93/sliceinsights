# Migration Plan: Railway PostgreSQL → Supabase

**Date:** 2026-03-21  
**Status:** Planning  
**Goal:** Migrar do Railway PostgreSQL para Supabase para resolver problemas de conexão e ganhar recursos adicionais (Auth, API automática, Realtime).

---

## 1. Executive Summary

| Aspect | Current (Railway) | Target (Supabase) |
|--------|-------------------|-------------------|
| **Database** | Railway PostgreSQL | Supabase PostgreSQL |
| **Connection** | TCP (unreliable) | HTTPS (stable) |
| **Auth** | Manual | Supabase Auth (50K MAU free) |
| **API** | FastAPI manual | Auto-generated REST |
| **Realtime** | Não | Supabase Realtime |

### Benefícios Esperados
- Conexão mais estável (HTTPS vs TCP)
- Auth built-in (elimina código manual)
- API automática (menos código backend)
- Realtime dashboards
- Branching para dev/test

---

## 2. Escopo da Migração

### 2.1 Componentes a Migrar

| Componente | Arquivos | Esforço |
|------------|----------|---------|
| **Config** | `app/config.py` | 1h |
| **Database Client** | `app/db/database.py` | 4h |
| **Models** | `app/models/*.py` (12 files) | 8h |
| **API Routes** | `app/api/routes.py` | 6h |
| **API Endpoints** | `app/api/endpoints/*.py` | 8h |
| **Services** | `app/services/*.py` | 4h |
| **Scripts** | `scripts/*.py` (35 files) | 24h |
| **Tests** | `tests/*.py` | 4h |

**Total Estimado:** ~60 horas

---

## 3. Plano de Migração (Fases)

### Fase 1: Setup Supabase (2h)

```
[ ] Criar projeto no Supabase (supabase.com)
[ ] Obter connection string (DATABASE_URL)
[ ] Configurar projeto local com supabase CLI
[ ] Testar conexão básica
```

**Arquivos alterados:**
- `.env` (nova DATABASE_URL)
- GitHub Secrets (DATABASE_URL_SYNC)

---

### Fase 2: Adapter de Banco (4h)

Criar camada de abstração para suportar ambos:

```python
# app/db/supabase_client.py (NOVO)
from supabase import create_client, Client

_supabase_client: Client = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
    return _supabase_client
```

**Decisão de Arquitetura:**
- Manter SQLModel como ORM (suporta PostgreSQL)
- Substituir só a connection string
- Adicionar retry logic para Supabase client

---

### Fase 3: Models (8h)

| Model | Ação | Esforço |
|-------|------|---------|
| `brand.py` | Keep SQLModel + RLS | 30m |
| `paddle.py` | Keep SQLModel + RLS | 1h |
| `market_offer.py` | Keep SQLModel + RLS | 30m |
| `store.py` | Keep SQLModel + RLS | 30m |
| `slo.py` | Keep SQLModel + RLS | 30m |
| `slo_alert.py` | Keep SQLModel + RLS | 30m |
| `deploy_log.py` | Keep SQLModel + RLS | 30m |
| `quality_metric.py` | Keep SQLModel + RLS | 30m |
| `price_snapshot.py` | Keep SQLModel + RLS | 30m |
| `price_alert.py` | Keep SQLModel + RLS | 30m |
| `lead.py` | Keep SQLModel + RLS | 30m |
| `ai_knowledge.py` | Keep SQLModel + RLS | 30m |

**Estratégia:**
- SQLModel funciona com Supabase (é PostgreSQL)
- Adicionar Row Level Security (RLS) policies
- Usar same JSONB, ARRAY, pgvector features

---

### Fase 4: Scripts (24h)

Scripts que usam banco (ordem por prioridade):

| Script | Ação | Prioridade |
|--------|------|------------|
| `alert_worker.py` | Migrar para Supabase | **ALTA** |
| `slo_validator.py` | Migrar para Supabase | **ALTA** |
| `scrape_*.py` (12 files) | Migrar para Supabase | **ALTA** |
| `quality_aggregator.py` | Migrar para Supabase | MÉDIA |
| `deploy_worker.py` | Migrar para Supabase | MÉDIA |
| `ingest_*.py` (5 files) | Migrar para Supabase | MÉDIA |
| `measure_*.py` (2 files) | Migrar para Supabase | BAIXA |
| `audit_*.py` (2 files) | Migrar para Supabase | BAIXA |

**Estratégia:**
- Trocar `Session` por Supabase client
- Usar `.upsert()` para deduplicação
- Batch inserts com `.insert()` multi-row

---

### Fase 5: API Endpoints (14h)

| Endpoint | Ação | Esforço |
|----------|------|---------|
| `/paddles` | Manter (SQLModel) | 2h |
| `/search` | Manter (SQLModel) | 2h |
| `/recommendations` | Manter (SQLModel) | 2h |
| `/history` | Manter (SQLModel) | 2h |
| `/alerts` | Manter (SQLModel) | 2h |
| `/quality` | Manter (SQLModel) | 2h |
| `/leads` | Manter (SQLModel) | 2h |

**Estratégia:**
- SQLModel async funciona com Supabase
- Apenas mudar connection string

---

### Fase 6: GitHub Actions (2h)

```yaml
# .github/workflows/slo-check.yml
- name: Dispatch alerts
  env:
    DATABASE_URL_SYNC: ${{ secrets.DATABASE_URL_SYNC }}
    # Remover GOOGLE_APPLICATION_CREDENTIALS
```

---

## 4. Diferenças Técnicas

### 4.1 Connection String

| Provider | Format |
|----------|--------|
| Railway | `postgresql://user:pass@host:port/db` |
| Supabase | `postgresql://postgres:password@db.xxx.supabase.co:5432/postgres` |

### 4.2 Python Client

```python
# ANTES (Railway)
from sqlmodel import Session, select
from app.db.database import sync_engine

with Session(sync_engine) as session:
    results = session.exec(select(Paddle)).all()

# DEPOIS (Supabase)
# MESMO CÓDIGO - só muda connection string!
from sqlmodel import Session, select
from app.db.database import sync_engine

with Session(sync_engine) as session:
    results = session.exec(select(Paddle)).all()
```

**Benefício:** SQLModel é compatível com Supabase!

### 4.3 Novas Features (Opcionais)

```python
# Auth via Supabase
from supabase import create_client
supabase = create_client(url, key)
user = supabase.auth.sign_in_with_password(email, password)

# API Automática (sem FastAPI)
# Supabase já gera API REST:
# GET https://xxx.supabase.co/rest/v1/paddles

# Realtime subscriptions
channel = supabase.channel('db-changes')
  .on('postgres_changes', {'event': '*', 'table': 'slo_logs'}, handle)
  .subscribe()
```

---

## 5. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| RLS blocking access | Média | Alto | Testar local primeiro |
| Migration data loss | Baixa | Alto | Backup antes |
| Performance regression | Média | Médio | Query optimization |
| Breaking changes | Baixa | Médio | Test suite |

---

## 6. Step-by-Step

### Passo 1: Backup
```bash
# Exportar dados do Railway
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Passo 2: Criar Supabase
```bash
# Criar projeto no dashboard
# Obter connection string de: Settings → Database

# Testar locally
psql "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres" -c "SELECT 1"
```

### Passo 3: Atualizar Código
```bash
# Mudar .env
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
```

### Passo 4: Testar Local
```bash
python scripts/slo_validator.py --all
python scripts/alert_worker.py --all
```

### Passo 5: Deploy
```bash
git add .env.example
git commit -m "Migrate to Supabase"
git push origin main
```

---

## 7. Checklist de Migração

- [ ] Criar projeto Supabase
- [ ] Configurar GitHub Secrets (DATABASE_URL_SYNC)
- [ ] Testar conexão local
- [ ] Executar migration scripts (schema)
- [ ] Importar dados (se necessário)
- [ ] Testar API endpoints
- [ ] Testar scripts (alert_worker, scrapers)
- [ ] Testar GitHub Actions workflow
- [ ] Monitorar erros na primeira semana

---

## 8. Custos

| Recurso | Free Tier | Pago |
|---------|-----------|------|
| Database | 500 MB | $0.125/GB |
| Auth | 50K MAU | $0.003/MAU |
| Storage | 1 GB | $0.021/GB |
| API | Ilimitado | - |
| Realtime | 200 concurrent | $1/concurrent |

**Previsão:** R$ 0-50/mês (provavelmente free tier é suficiente)
