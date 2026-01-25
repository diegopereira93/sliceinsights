# SliceInsights - Documentação do Projeto

**Status**: Production-Ready | **Raquetes**: 460 | **Versão**: 1.6

> Plataforma premium de recomendação de raquetes de Pickleball com motor de IA e **Hyper-Personalização**, focada no mercado brasileiro.

---

## 🚀 Quick Start

### Para Desenvolvedores
1. **Executar localmente**: `docker compose up -d --build`
2. **Acessar**: 
   - Frontend: http://localhost:3000
   - API: http://localhost:8002/docs
3. **Consultar**: [`operations/runbook.md`](operations/runbook.md) para troubleshooting

### Para Deploy
- **Railway**: Siga [`operations/railway_deploy.md`](operations/railway_deploy.md)
- **Production Checklist**: [`roadmaps/production_readiness_roadmap.md`](roadmaps/production_readiness_roadmap.md) ✅

---

## 📚 Navegação da Documentação

### 🔧 Documentação Técnica
| Documento | Descrição |
|-----------|-----------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Visão geral da arquitetura, stack e fluxo |
| [`technical/database_schema.md`](technical/database_schema.md) | Schema PostgreSQL detalhado |
| [`technical/api_specification.md`](technical/api_specification.md) | Endpoints, requests e responses |
| [`technical/quiz.md`](technical/quiz.md) | Lógica do quiz de recomendação (10 perguntas) |
| [`technical/hyper_personalization.md`](technical/hyper_personalization.md) | Sistema de Hyper-Personalização (Ideal Point, Delta Score) |

### ⚙️ Operações
| Documento | Descrição |
|-----------|-----------|
| [`operations/runbook.md`](operations/runbook.md) | Troubleshooting e manutenção |
| [`operations/railway_deploy.md`](operations/railway_deploy.md) | Tutorial de deploy no Railway |

### 🗺️ Roadmaps Estratégicos (Pareto 80/20)
| Documento | Status | Descrição |
|-----------|--------|-----------|
| [`roadmaps/NEXT_STEPS.md`](roadmaps/NEXT_STEPS.md) | 🔥 **URGENTE** | O que fazer AGORA (P0/P1) |
| [`roadmaps/monetization.md`](roadmaps/monetization.md) | 🟡 20% | Foco em geração de receita |
| [`roadmaps/future_ideas.md`](roadmaps/future_ideas.md) | 💡 Backlog | Ideias não priorizadas |

---

---

## 🎯 Estado Atual do Projeto

### ✅ **Implementado**
- 🗄️ **Catálogo**: 460 raquetes, ~50 marcas
- 🧠 **Algoritmo**: Smart scoring, value score, slider Power/Control
- 📊 **Estatísticas**: Hub de inteligência de mercado completo
- 🔒 **Produção**: Rate limiting, CORS, logging, métricas Prometheus
- ⚔️ **Features**: Comparador "Batalha", Info tooltips técnicos
- ✅ **Testes**: 15 testes automatizados passando
- 🎯 **Hyper-Personalização (v1.6)**:
  - Quiz de 10 perguntas com slider Power/Control
  - **Ideal Point**: Seu perfil ideal visualizado nos gráficos de dispersão
  - **Delta Score (%)**: Distância entre suas preferências e cada raquete
  - Persistencia de sessão para análises personalizadas

### 🟡 **Em Progresso**
- 💰 Monetização (afiliados Amazon/ML, AdSense)
- 📱 PWA com favoritos offline
- 🧮 Calculadora de importação

### 📋 **Planejado**
- 🤖 Scraper automatizado para e-commerce BR
- ⏰ Alertas de preço
- ⭐ Sistema de reviews

---

## 📊 Métricas de Progresso

| Categoria | Progresso | Meta |
|-----------|-----------|------|
| MVP Features | 100% | ✅ Completo |
| Catálogo | 460 raquetes | 🟢 920% da meta (50) |
| Production Ready | 100% | ✅ Completo |
| Monetização | 20% | 🟡 Em progresso |

---

## 🏗️ Tech Stack

- **Frontend**: Next.js 15 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI + SQLModel + AsyncPG
- **Database**: PostgreSQL 16
- **Deploy**: Docker + Railway
- **Observability**: Prometheus + Sentry + Structlog

---

## 📁 Estrutura de Diretórios

```
sliceinsights/
├── app/              # FastAPI backend
├── frontend/         # Next.js frontend
├── tests/            # Testes automatizados
├── scripts/          # Scripts de utilidade (seeding, scraping)
├── data/             # Dados de paddles (CSV)
├── docs/             # Documentação (você está aqui!)
│   ├── technical/    # Specs técnicas
│   ├── operations/   # Deploy e manutenção
│   ├── roadmaps/     # Planejamento estratégico
│   └── archive/      # Documentos históricos
└── docker-compose.yml
```

---

## 🔗 Links Úteis

- **Swagger API**: http://localhost:8002/docs (dev)
- **Métricas**: http://localhost:8002/metrics
- **Health Check**: http://localhost:8002/api/v1/health

---

## 📝 Contribuindo

1. Consulte [`ARCHITECTURE.md`](ARCHITECTURE.md) para entender a estrutura
2. Revise roadmaps em [`roadmaps/`](roadmaps/) para próximos passos
3. Execute testes: `docker compose exec backend_v3 pytest tests/ -v`

---

## 📜 Licença

MIT

---

**Última Atualização**: Janeiro 2026 | **Versão**: 1.6 (Hyper-Personalization)
