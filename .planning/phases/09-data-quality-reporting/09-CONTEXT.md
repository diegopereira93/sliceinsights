# Phase 9: Data Quality Checks & Reporting - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Monitoramento contínuo de qualidade do pipeline — job horário para os 11 scrapers ativos, persistência de métricas históricas em banco, endpoint de dashboard para consulta em tempo real, e relatório semanal de tendências com detecção de anomalias. Alertas operacionais em tempo real são cobertura da Fase 7 e estão fora do escopo desta fase.

</domain>

<decisions>
## Implementation Decisions

### Modelo de Dados (quality_metrics)
- Criar nova tabela `quality_metrics` — separar de `slo_logs` (SLO = alertas operacionais; QC = tendências históricas)
- 5 métricas por scraper por execução: `freshness_hours`, `completeness_pct` (% campos preenchidos por produto), `coverage_pct` (% campos preenchidos), `product_count`, `error_rate`
- Granularidade: uma linha por scraper por execução do workflow (não agregado por hora)
- Campo `run_id` obrigatório — correlaciona com GitHub Actions run number para debugging de incidentes
- Retenção indefinida (sem purge automático por enquanto)

### Dashboard Endpoint
- Rota: `GET /api/quality/dashboard` — consistente com padrão existente em `app/api/routes.py`
- Endpoint público, sem autenticação
- Retorna snapshot mais recente por scraper (não histórico)
- Estrutura de resposta: lista de scrapers com métricas + campo `status` global consolidado
  - `healthy` = todos passando
  - `degraded` = 1-2 falhando
  - `critical` = 3+ falhando
- Cache in-memory de 5 minutos (atualização horária torna cache de 5min suficiente)
- Formato JSON por scraper:
  ```json
  {
    "status": "degraded",
    "scrapers": [
      {
        "name": "mercado_livre",
        "freshness_hours": 2.5,
        "completeness_pct": 84.2,
        "coverage_pct": 91.0,
        "product_count": 312,
        "error_rate": 0.0,
        "status": "pass",
        "last_checked": "2026-03-20T14:00:00Z"
      }
    ],
    "summary": {
      "total_scrapers": 11,
      "passing": 9,
      "failing": 2
    }
  }
  ```

### Relatório Semanal
- Formato: HTML email (reutiliza padrão de SLOAlertService da Fase 7)
- Canal: apenas email — mesmo `admin_email_group` já configurado na Fase 7
- Schedule: segunda-feira 08:00 UTC (`cron: '0 8 * * 1'`), cobrindo a semana anterior
- Definição de anomalia: queda > 10% em qualquer métrica comparado à semana anterior
- Trend: tabela HTML com 4 semanas de dados + setas ↑↓ por métrica (sem matplotlib — tabela HTML pura)
- Estrutura do email: seções separadas "⬆ Melhorando" e "⬇ Degradando" para facilitar triagem

### Integração do Audit Horário
- Criar novo `scripts/quality_aggregator.py` — não modificar `audit_data_quality.py` (que é ferramenta de auditoria manual)
- Workflow `quality-audit.yml`: matrix strategy com um job por scraper rodando em paralelo
- Step de consolidação ao final: após todos os jobs da matrix, um job `consolidate` salva um registro global com run_id e status agregado
- run_id injetado via env var (`GITHUB_RUN_ID`) em cada job paralelo para correlação
- Triggers: `schedule` (cron horário) + `workflow_dispatch` (trigger manual para debugging)
- Falhas de scraper individual: apenas persistência no banco — sem alertas imediatos (SLO já cobre alertas operacionais)

### Claude's Discretion
- Schema exato da tabela `quality_metrics` (tipos de coluna, índices)
- Lógica de cálculo de `coverage_pct` por produto (quais campos contar)
- Implementação do cache in-memory (dict simples vs functools.lru_cache vs biblioteca)
- Template HTML do email do relatório (cores, layout)
- Cálculo do `error_rate` por scraper (janela de tempo: últimas 24h)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Specifications
- `.planning/REQUIREMENTS.md` §Data Quality Checks & Reporting — QC-01 a QC-06, acceptance criteria completos
- `.planning/ROADMAP.md` §Phase 9 — deliverables esperados, success criteria

### Prior Phase Context
- `.planning/phases/07-alerts-and-monitoring/07-CONTEXT.md` — canais de alerta (Telegram, GitHub Issues, Email), SLOAlertService, admin_email_group
- `.planning/phases/08-deploy-release-strategy/08-CONTEXT.md` — padrões de workflow, deploy_worker.py, run_scraper.py

### Architecture & Code Existente
- `app/models/slo.py` — SLOLog schema (referência para criar quality_metrics seguindo mesmo padrão SQLModel)
- `app/services/slo_alerts.py` — SLOAlertService com send_email; reutilizar para envio do relatório semanal
- `scripts/audit_data_quality.py` — script de auditoria manual existente (NÃO modificar; referência apenas)
- `scripts/run_scraper.py` — padrão de entry point de scripts
- `app/api/routes.py` — padrão de registro de rotas FastAPI
- `.github/workflows/slo-check.yml` — padrão de workflow com cron + workflow_dispatch + matrix

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/models/slo.py` → `SLOLog`: modelo SQLModel com JSONB — mesmo padrão para `QualityMetric`
- `app/services/slo_alerts.py` → `SLOAlertService.send_email()`: envio de email com template HTML; reutilizar para relatório semanal
- `scripts/audit_data_quality.py`: lógica de cálculo de freshness e completeness já implementada; extrair como referência
- `pandas==2.2.0`: já no requirements.txt — disponível para agregações e cálculo de tendências

### Established Patterns
- Workflows com matrix strategy: já usado em `ci.yml` para testes paralelos
- Cron + workflow_dispatch: padrão em `slo-check.yml` e `deploy-nightly.yml`
- SQLModel com JSONB para campos extras: padrão em `SLOLog.details`
- FastAPI routes em `app/api/routes.py`: onde registrar o novo endpoint de dashboard

### Integration Points
- `app/api/routes.py`: registrar `GET /api/quality/dashboard`
- `alembic/`: nova migration para tabela `quality_metrics`
- `app/db/database.py`: session factory já configurada; quality_aggregator.py usará mesma sessão
- `.github/workflows/`: adicionar `quality-audit.yml` e ajustar `quality-report.yml` (semanal)

</code_context>

<specifics>
## Specific Ideas

- Dashboard JSON exato foi aprovado durante a discussão (ver seção Dashboard Endpoint acima)
- Relatório semanal: tabela HTML 4 semanas com setas ↑↓, sem gráficos matplotlib
- Email report: dois blocos visuais distintos — "⬆ Melhorando" (verde) e "⬇ Degradando" (vermelho)

</specifics>

<deferred>
## Deferred Ideas

- Nenhuma — discussão ficou dentro do escopo da fase

</deferred>

---

*Phase: 09-data-quality-reporting*
*Context gathered: 2026-03-20*
