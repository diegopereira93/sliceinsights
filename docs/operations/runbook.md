# Runbook: Operação e Manutenção - SliceInsights

Instruções fundamentais para rodar, manter e depurar o projeto SliceInsights.

## 🐳 1. Operação com Docker

O projeto utiliza o Docker Compose para orquestrar 4 serviços principais.

### Serviços:
- `postgres_v3`: PostgreSQL 16 (Porta 5434).
- `backend_v3`: FastAPI Backend (Porta 8002).
- `frontend_next`: Next.js Frontend (Porta 3000).

### Comandos de Gestão:
```bash
# Subir ambiente (Background)
docker compose up -d

# Visualizar logs em tempo real
docker compose logs -f

# Logs de um serviço específico
docker compose logs -f backend_v3

# Reiniciar um serviço específico
docker compose restart frontend_next

# Rebuild completo (após mudanças em requirements.txt ou package.json)
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Operações Internas:
Se precisar rodar comandos dentro dos containers:
```bash
# Acessar terminal do backend
docker exec -it backend_v3 bash

# Ver status do banco de dados
docker exec -it postgres_v3 pg_isready -U postgres

# Rodar testes
docker exec -it backend_v3 pytest tests/ -v
```

---

## 🏭 2. Deploy de Produção

Para deploy em produção, use o arquivo `docker-compose.prod.yml`:

```bash
# Build e deploy de produção
docker compose -f docker-compose.prod.yml up -d --build

# Verificar status
docker compose -f docker-compose.prod.yml ps

# Ver logs
docker compose -f docker-compose.prod.yml logs -f
```

### Variáveis de Ambiente Obrigatórias:
Copie `.env.example` para `.env` e configure:

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | Senha do banco (MUDAR EM PRODUÇÃO!) |
| `ALLOWED_ORIGINS` | Origens CORS permitidas |
| `SENTRY_DSN` | DSN do Sentry para error tracking |
| `LOG_LEVEL` | Nível de log (INFO, DEBUG, WARNING) |

---

## 💾 3. Dados e Persistência

### Popular Base de Dados (Seed):
O serviço `seed_v3` roda automaticamente no `docker compose up`. Se precisar rodar manualmente:
```bash
docker exec -it backend_v3 python -m app.db.seed_brazil_catalog
```

### Limpar e Reiniciar Banco:
```bash
docker compose down -v
docker compose up -d
```

---

## 📈 4. Monitoramento e Observabilidade

### Endpoints de Monitoramento:
| Endpoint | Descrição |
|----------|-----------|
| `http://localhost:8002/api/v1/health` | Health check com status do DB |
| `http://localhost:8002/metrics` | Métricas Prometheus |
| `http://localhost:8002/docs` | Swagger API Documentation |

### Logs Estruturados:
Os logs são estruturados em JSON (em produção) para fácil parsing:
```bash
# Ver logs estruturados
docker compose logs -f backend_v3 | jq '.'
```

### Rate Limiting:
Limites configurados por endpoint:
- `/recommendations`: 30 req/min
- `/search`: 60 req/min
- `/paddles`: 100 req/min

---

## 🔧 5. Fluxo de Desenvolvimento (Hot-Reload)

Não é necessário instalar Python ou Node localmente para desenvolver. O `docker-compose.yml` está configurado com **Volumes**, o que permite que mudanças no código sejam refletidas instantaneamente nos containers.

### Como funciona:
- **Backend**: A pasta `./app` está mapeada. O servidor `uvicorn` roda com `--reload`.
- **Frontend**: A pasta `./frontend` está mapeada. O comando `npm run dev` gerencia o hot-reload da UI.

### Dica de Produtividade:
Ao editar um arquivo `.tsx` ou `.py` na sua IDE (VS Code, etc), salve o arquivo e observe os logs do Docker (`docker compose logs -f`). Você verá o servidor reiniciando ou o Next.js recompilando automaticamente.

---

## 🧪 6. Testes

### Backend Tests:
```bash
# Rodar todos os testes
docker exec -it backend_v3 pytest tests/ -v

# Rodar com coverage
docker exec -it backend_v3 pytest tests/ -v --cov=app
```

### Frontend E2E Tests:
```bash
# Instalar Playwright (primeira vez)
cd frontend && npx playwright install

# Rodar testes E2E
npx playwright test

# Ver report visual
npx playwright show-report
```

---

## 🚑 7. Troubleshooting (Problemas Comuns)

### Conflito de Porta (8000/3000):
- Verifique se não há containers antigos: `docker ps`.
- A porta da API foi mapeada para **8002** no `docker-compose.yml` v3 para evitar conflitos.

### Erro de Conexão DB (AsyncPG):
- Garanta que o container `postgres_v3` está `healthy`.
- Verifique a string `DATABASE_URL` no `.env`.

### Docker Permission Denied:
- Se estiver usando Snap, considere migrar para a instalação via `apt`.
- Tente rodar com `sudo` se o seu usuário não estiver no grupo `docker`.

### Rate Limit Exceeded (429):
- Aguarde 1 minuto para o limite resetar.
- Se necessário, ajuste os limites em `app/api/routes.py`.

### Health Check Failing (503):
- Verifique se o banco de dados está running: `docker ps`.
- Teste a conexão: `docker exec -it postgres_v3 pg_isready -U postgres`.

---

## 🔐 8. Segurança

### CORS:
Origens permitidas são configuradas via `ALLOWED_ORIGINS` no `.env`. Em produção, configure apenas os domínios necessários.

### Credenciais:
- Nunca commite senhas reais no `.env`.
- Use `.env.example` como template.
- Em produção, use secrets management (AWS Secrets Manager, etc).

### Sentry:
Configure `SENTRY_DSN` para capturar erros automaticamente:
```bash
SENTRY_DSN=https://xxx@sentry.io/xxx
```
