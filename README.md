# SliceInsights - Insights precisos para sua melhor jogada

![CI Quality Gate](https://github.com/diegogp/sliceinsights/actions/workflows/production-pipeline.yml/badge.svg)


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
- **Health Check**: Validação de conexão com DB em `/api/v1/health` (Returns 503 on failure)
- **Error Boundaries**: Tratamento gracioso de erros no frontend
- **E2E Testing**: Suite completa com Playwright verificando integridade de dados em produção
### Estrutura de Monorepo (Frontend/Backend)
- O frontend reside na pasta `/frontend`.
- O deploy na Vercel é configurado via DashBoard (Root Directory: `frontend`) e o arquivo `frontend/vercel.json` gerencia variáveis de ambiente.
- O pipeline de CI/CD no GitHub Actions dispara o deploy a partir da raiz para garantir a detecção correta.
- [x] **CI/CD Pipeline**: GitHub Actions para testes e build
- [x] **Lógica de Recomendação**: Validação física unificada (Physics-Based Scoring)
- [x] **Verificação Contínua**: Ralph-Loop (Self-Healing) ativo em produção

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
# SliceInsights 🎾🇧🇷

**Recomendador inteligente de raquetes de pickleball focado no mercado brasileiro**

SliceInsights é uma plataforma que ajuda jogadores brasileiros a encontrar a raquete de pickleball ideal através de um quiz personalizado e análises de mercado baseadas em dados reais.

## 🌟 Destaques

- 🇧🇷 **Foco Brasil**: Catálogo com 37 raquetes disponíveis no mercado brasileiro
- 📊 **Analytics Global**: 495 raquetes no banco para análises de mercado completas
- 🖼️ **Imagens HD**: Produtos com fotos em alta resolução (WebP 1024x1024)
- 🤖 **Recomendação Inteligente**: Quiz de 10 perguntas + algoritmo de scoring
- 🤖 **Motor de Recomendação Smart**: Algoritmo que unifica notas técnicas (0-10) com base em Física (Twist Weight, Spin RPM) e alinhamento com estilo de jogo (Power, Control, Balanced).
- 💰 **Preços Reais**: Integração com Brazil Pickleball Store
- 📈 **Market Intelligence**: Estatísticas e tendências do mercado global

## 🏗️ Arquitetura

### Stack Tecnológica

- **Backend**: FastAPI + SQLModel + PostgreSQL
- **Frontend**: Next.js 14 + TypeScript + shadcn/ui
- **Scrapers**: Playwright (Python)
- **Deployment**: Docker Compose

### Estratégia Híbrida de Dados

O projeto utiliza uma abordagem em duas camadas:

1. **Catálogo de Produtos** (`available_in_brazil=true`)
   - 37 raquetes disponíveis no Brasil
   - Preços em BRL (reais)
   - Imagens em alta resolução
   - Links diretos para lojas brasileiras

2. **Analytics e Estatísticas** (dataset completo)
   - 495 raquetes de todo o mundo
   - Dados técnicos detalhados
   - Comparações de mercado global

## 🚀 Quick Start

### Pré-requisitos

- Docker e Docker Compose
- Python 3.11+ (para scrapers)
- Node.js 18+ (para desenvolvimento frontend)

### Executar o Projeto

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/sliceinsights.git
cd sliceinsights

# Subir todos os serviços
docker compose up -d

# Popular o banco de dados
docker compose exec backend_v3 python -m app.db.seed_data_hybrid

# Acessar aplicação
# Frontend: http://localhost:3000
# API: http://localhost:8002
# Docs API: http://localhost:8002/docs
```

### Estrutura de Serviços

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| `frontend_next` | 3000 | Aplicação Next.js |
| `backend_v3` | 8002 | API FastAPI |
| `postgres_v3` | 5434 | Banco PostgreSQL |

## 📊 Scrapers de Dados

### Brazil Pickleball Store

Scraper automatizado que extrai produtos da loja oficial:

```bash
# Executar scraper
docker compose --profile tools run --rm scraper python scripts/scrape_brazil_store.py

# Output: data/raw/brazil_pickleball_store.csv
```

**Dados extraídos**:
- Nome da marca e modelo
- Preço em BRL
- URL do produto
- Imagem em alta resolução (WebP)

### Atualizar Banco de Dados

Após executar os scrapers:

```bash
# Repopular banco com novos dados
docker compose exec backend_v3 python -m app.db.seed_data_hybrid
```

O seed híbrido:
1. Cria produtos brasileiros primeiro (COM imagens)
2. Adiciona produtos internacionais (para analytics)
3. Evita duplicatas automaticamente

## 🎯 Funcionalidades

### Quiz de Recomendação

Sistema inteligente de 10 perguntas que considera:
- Nível de habilidade
- Estilo de jogo (potência vs controle)
- Histórico esportivo (tênis, etc.)
- Orçamento em reais
- Preferências de peso e formato

### Market Intelligence

- 📉 Distribuição de preços no mercado
- 📊 Segmentação por características técnicas
- 💎 "Hidden Gems" - melhores custo-benefício
- 🏷️ Análise por marca

### Catálogo Brasileiro

- Filtros por marca, preço, características
- Comparação lado a lado (Battle Mode)
- Detalhes técnicos completos
- Links diretos para compra

## 📁 Estrutura do Projeto

```
sliceinsights/
├── app/                      # Backend FastAPI
│   ├── api/                  # Endpoints REST
│   ├── db/                   # Database & ORM
│   │   ├── seed_data_hybrid.py  # Seed híbrido
│   │   └── database.py
│   ├── models/               # SQLModel schemas
│   └── main.py
├── frontend/                 # Frontend Next.js
│   ├── app/                  # App router
│   ├── components/           # React components
│   └── lib/                  # Utilities
├── scripts/                  # Scrapers & tools
│   ├── scrape_brazil_store.py
│   └── scrape_mercado_livre.py
├── data/                     # Dados extraídos
│   └── raw/
│       ├── brazil_pickleball_store.csv
│       └── paddle_stats_dump.csv
└── docker-compose.yml
```

## 🔧 Desenvolvimento

### Backend

```bash
# Entrar no container
docker compose exec backend_v3 bash

# Rodar testes
pytest

# Criar migração
alembic revision --autogenerate -m "description"
```

### Frontend

```bash
# Desenvolvimento local
cd frontend
npm install
npm run dev

# Build de produção
npm run build
```

### Qualidade & Testes

```bash
# Verificar todo o projeto (Lint, Segurança, Testes)
./scripts/verify.sh

# Rodar apenas Linter (Ruff)
./.venv/bin/ruff check .

# Rodar Scan de Segurança
./.venv/bin/safety check -r requirements.txt
```

### 🌳 Fluxo de Trabalho Git (Obrigatório)

Para garantir a estabilidade em produção, todos os ajustes (humanos ou agentes) seguem este padrão:

1.  **Branch a partir da `main`**: `git checkout -b feat/nome-da-feature`.
2.  **Desenvolvimento**: Implemente as mudanças e verifique localmente com `./scripts/verify.sh`.
3.  **Documentação**: Atualize todos os documentos afetados (README, API docs) antes do push.
4.  **Pull Request**: Abra um PR contra a `main`. **Nunca faça push direto na `main`.**
5.  **Merge**: O merge só deve ocorrer após aprovação e sucesso na pipeline de CI.

**Padrões exigidos**:
- **Linting**: Código deve passar no `ruff` sem erros.
- **Segurança**: Dependências verificadas pelo `safety`.
- **Testing**: Cobertura básica de endpoints críticos.

## 📝 API Endpoints

### Principais Rotas

```bash
# Listar produtos brasileiros (padrão)
GET /api/v1/paddles

# Todas as raquetes (analytics)
GET /api/v1/paddles?available_in_brazil=null

# Apenas internacionais
GET /api/v1/paddles?available_in_brazil=false

# Recomendações do quiz
POST /api/v1/recommendations
```

## 🤖 Desenvolvimento Autônomo

Este projeto utiliza um enxame de agentes de IA especializados para acelerar o desenvolvimento.

**Leia o guia completo: [AUTONOMOUS_DEV.md](./AUTONOMOUS_DEV.md)**

### Workflow Rápido (IssueOps)
1.  **Abra uma Issue** usando os templates (`Feature Request`, `Bug Report`).
2.  **Marque um Agente** (ex: `@project-planner`) para iniciar o trabalho.
3.  **Revise o PR** gerado automaticamente.

### Agentes Principais
*   `@project-planner`: Planejamento e Arquitetura.
*   `@frontend-specialist`: UI/UX e React.
*   `@backend-specialist`: API e Banco de Dados.
*   `@devops-engineer`: CI/CD e Infra.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch de feature (`git checkout -b feat/nova-feature`)
3. Commit suas mudanças (`git commit -m 'feat: adiciona nova feature'`)
4. Push para a branch (`git push origin feat/nova-feature`)
5. Abra um Pull Request contra a `main`.

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🙏 Agradecimentos

- Brazil Pickleball Store pela disponibilidade dos produtos
- Comunidade brasileira de pickleball
- Dataset internacional de especificações técnicas

---

**Desenvolvido com ❤️ para a comunidade brasileira de pickleball**
