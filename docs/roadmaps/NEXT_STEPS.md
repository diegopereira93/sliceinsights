# NEXT STEPS - SliceInsights v1.7+

> **Última Atualização:** Janeiro 2026 | **Princípio:** Pareto 80/20

---

## 🔥 P2 - Próxima Onda (Monitoramento Real)

| Tarefa | Valor | Esforço |
|--------|-------|---------|
| **Scraper Engine** | Muito Alto | Alto |
| **Histórico de Preços** | Alto | Médio |

### Scraper Engine & Crawler
- Monitoramento automático de preços em lojas reais.
- Crawler agendado (Cron Job) para buscar dados de Amazon/ML.
- **Objetivo:** Substituir dados estáticos por dinâmicos.

### Histórico de Preços (Time-Series)
- Persistência diária de preços em tabela SQL `price_history`.
- Substituir gráfico "mockado" por dados reais.

---

## ✅ Concluído (v1.7 - Janeiro 2026)

- [x] **P0: Deployment Stack (100% Gratuito)**
  - Frontend: Vercel (https://sliceinsights.vercel.app)
  - Backend: Render (Free Tier)
  - Database: Neon Serverless Postgres (US East)
- [x] **P0: Infrastructure as Code**
  - `render.yaml` para deploy automático
  - `vercel.json` para build otimizado
  - Documentação completa em `DEPLOY_INSTRUCTIONS.md`
- [x] **P0: Security Fixes**
  - JS Injection em scripts corrigido
  - SQL Injection verificado (ORM seguro)
  - CORS configurado corretamente

## ✅ Concluído (v1.6)

- [x] **P1: PWA (Progressive Web App)** - Offline + Install
- [x] **P1: Sistema de Inscrição em Alertas** (DB + UI)
- [x] **P0: Calculadora de Importação**
- [x] **P0: Links de Afiliados (Amazon/ML)**
- [x] Hyper-Personalização (Ideal Point, Delta Score)
- [x] Statistics Page & Battle Mode
- [x] Production Readiness (rate limiting, logging, Prometheus)
- [x] E2E Testing with Playwright (Verify Live Deployment)
