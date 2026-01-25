# NEXT STEPS - SliceInsights v1.6+

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

## ✅ Concluído (v1.6)

- [x] **P1: PWA (Progressive Web App)** - Offline + Install
- [x] **P1: Sistema de Inscrição em Alertas** (DB + UI)
- [x] **P0: Calculadora de Importação**
- [x] **P0: Links de Afiliados (Amazon/ML)**
- [x] Hyper-Personalização (Ideal Point, Delta Score)
- [x] Statistics Page & Battle Mode
- [x] Production Readiness (rate limiting, logging, Prometheus)
