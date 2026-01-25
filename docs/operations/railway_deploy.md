# Railway Deployment Guide - Niterói Raquetes

Guia completo para deploy gratuito no Railway (Front + Back + DB no mesmo lugar).

## 📋 Pré-requisitos

1. Conta no [Railway](https://railway.app/) (login com GitHub)
2. Repositório no GitHub

---

## 🚀 Deploy em 5 Passos

### 1. Criar Projeto no Railway

1. Acesse [railway.app/new](https://railway.app/new)
2. Selecione **"Deploy from GitHub repo"**
3. Conecte seu repositório

### 2. Adicionar PostgreSQL

1. No dashboard do projeto, clique **"+ New"**
2. Selecione **"Database" → "PostgreSQL"**
3. Railway irá provisionar automaticamente

### 3. Configurar Variáveis de Ambiente

No serviço **Backend**, adicione:

```env
# Database (Railway injeta automaticamente)
DATABASE_URL=${{Postgres.DATABASE_URL}}
DATABASE_URL_SYNC=${{Postgres.DATABASE_URL | replace("postgresql+asyncpg://", "postgresql://")}}

# App Config
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://seu-projeto.up.railway.app

# Optional
SENTRY_DSN=
```

No serviço **Frontend**, adicione:

```env
NEXT_PUBLIC_API_URL=https://seu-backend.up.railway.app/api/v1
```

### 4. Configurar Build Commands

**Backend (FastAPI):**
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Frontend (Next.js):**
- Build: `cd frontend && npm ci && npm run build`
- Start: `cd frontend && npm start`

### 5. Deploy!

Railway detecta automaticamente os commits e faz deploy.

---

## 📁 Estrutura de Serviços no Railway

```
┌─────────────────────────────────────────────────┐
│                 RAILWAY PROJECT                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   Backend   │  │  Frontend   │  │Postgres │ │
│  │   FastAPI   │  │   Next.js   │  │   DB    │ │
│  │  Port 8000  │  │  Port 3000  │  │         │ │
│  └─────────────┘  └─────────────┘  └─────────┘ │
│        │                │               │       │
│        └────────────────┴───────────────┘       │
│                    Linked                       │
└─────────────────────────────────────────────────┘
```

---

## 💾 Migrar Base de Dados

Após o primeiro deploy, execute as migrations:

```bash
# Via Railway CLI
railway run alembic upgrade head

# Ou via shell no dashboard
python -m app.db.seed_data
```

---

## 🔗 URLs Geradas

Após deploy, Railway gera URLs como:
- **Frontend**: `https://seu-projeto-production.up.railway.app`
- **Backend**: `https://seu-projeto-backend-production.up.railway.app`

---

## 💰 Custos

| Tier | Crédito | Notas |
|------|---------|-------|
| Trial (30 dias) | $5 grátis | Suficiente para MVP |
| Free (após trial) | $1/mês | Para uso mínimo |
| Hobby | $5/mês | Recomendado para produção leve |

---

## ⚠️ Troubleshooting

### Build Falha
- Verifique se `requirements.txt` está na raiz
- Para frontend, verifique se `package.json` existe em `/frontend`

### Conexão com DB Falha
- Confirme que a variável `DATABASE_URL` está usando a referência `${{Postgres.DATABASE_URL}}`
- Railway injeta a URL automaticamente

### CORS Errors
- Atualize `ALLOWED_ORIGINS` com a URL do frontend gerada pelo Railway
