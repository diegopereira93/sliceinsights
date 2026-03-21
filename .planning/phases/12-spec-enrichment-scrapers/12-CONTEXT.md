# Phase 12: Spec Enrichment Scrapers - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Enriquecer os 10 scrapers existentes para capturar specs técnicas (`core_thickness_mm`, `face_material`, `weight_grams`, `shape`) de páginas das lojas brasileiras e executar automaticamente toda semana via novo GitHub Actions workflow — elevando a completude de specs de 0% para ≥70%.

Fora do escopo desta fase: API de catálogo (Phase 13), front-end (Phase 14), assistente de IA (Phase 15), retry logic nos scrapers de preço existentes.

</domain>

<decisions>
## Implementation Decisions

### Fonte de verdade das specs
- Specs válidas **somente** se extraídas das páginas das lojas brasileiras
- Dados do mercado americano (`enrichment.py`, fuzzy match via dumps externos) **não contam** para a meta de 70%
- **`enrichment.py` será arquivado** — catálogo começa do zero com dados 100% provenientes do scraping BR
- Estratégia de extração: dados estruturados (tabela de specs) primeiro; texto livre (regex/parsing) como fallback
- Fonte dos dados registrada em `validation_sources` ao salvar (ex: `scraping_joola`, `scraping_prospin`)

### Qualidade mínima aceita
- Enriquecer um paddle **somente** se os 4 campos estiverem presentes: `core_thickness_mm`, `face_material`, `weight_grams`, `shape`
- Specs parciais (1-3 campos) não são salvas neste ciclo — produto permanece sem specs
- Meta de 70% = 70% dos paddles em `paddle_master` com os **4 campos preenchidos** após um ciclo completo
- Dados de lojas BR têm prioridade absoluta: sobrescrever qualquer valor anterior (inclusive dados americanos) quando os 4 campos são encontrados

### Confiabilidade do cron
- Falha de scraper = exceção Python não capturada; specs vazias/incompletas são resultado válido, não falha
- Workflow: `continue-on-error: true` por scraper — falha em uma loja não bloqueia as demais
- Resultado esperado: ≥8 de 10 scrapers sem exceção (80% pass rate, conforme ROADMAP)
- Após ciclo completo de enriquecimento, o workflow dispara o quality audit para medir impacto nas specs
- Log de resultado por scraper (produtos enriquecidos, produtos sem specs encontradas, exceções)

### Arquitetura de enriquecimento
- **Passo separado após o scraping de preços**: scrapers de preço (`scrape_*.py`) permanecem focados em `brand_name`, `model_name`, `price_brl`, `product_url`, `image_url`
- `scrape_product_specs.py` evolui para cobrir as 10 lojas — torna-se o enriquecedor central
- Abordagem por loja: Claude analisa cada site e decide entre `requests`/BeautifulSoup (lojas simples/estáticas) ou Playwright (lojas com JS/Nuvemshop) — sem uma abordagem única forçada para todas
- Persistência diretamente no `paddle_master` via SQLModel session (sem JSON intermediário)
- `enrichment.py` arquivado junto com quaisquer referências a dumps americanos no pipeline

### Claude's Discretion
- Estratégia exata de HTML parsing por loja (seletores CSS, regex, JSON-LD, etc.)
- Ordem e lógica de fallback entre extração estruturada e texto livre
- Normalização de valores (ex: "16mm" → `16.0`, "Carbon Fiber" → `FaceMaterial.carbon`)
- Mapeamento de campos encontrados nas páginas para os enums `FaceMaterial` e `PaddleShape`
- Estrutura do job de quality audit no novo workflow (steps, paralelismo)

</decisions>

<canonical_refs>
## Canonical References

**Agentes downstream DEVEM ler antes de planejar ou implementar.**

### Requisitos desta fase
- `.planning/REQUIREMENTS.md` §Scraping — Lojas Especializadas — SCRP-02, SCRP-03, SCRP-04, SCRP-05, SCRP-06

### Modelos e enums relevantes
- `app/models/paddle.py` — `PaddleMasterBase` com campos de spec (`core_thickness_mm`, `face_material`, `shape`); enums `FaceMaterial`, `PaddleShape`
- `app/models/enums.py` — Valores aceitos para `FaceMaterial` e `PaddleShape`
- `app/db/ingestor.py` — Contrato de `ingest_rows()` (campos aceitos atualmente); entender antes de adicionar specs

### Scraper a evoluir
- `scripts/scrape_product_specs.py` — Implementação atual (Joola + BrazilPickleballStore, Playwright, escreve JSON); base para evoluir

### Scrapers de preço (referência de padrão)
- `scripts/scrape_pcklhouse.py` — Exemplo do padrão atual: `ingest_rows()`, `Store`, session

### Workflows existentes (referência)
- `.github/workflows/quality-audit.yml` — Padrão de matrix + `continue-on-error` a replicar no novo workflow

### Serviço a arquivar
- `app/services/enrichment.py` — Será arquivado; NÃO usar como fonte de specs nesta fase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scrape_product_specs.py`: já implementa extração com Playwright, parse de metafields (Joola) e texto livre (BrazilPickleballStore) — base direta para expandir para as 8 lojas restantes
- `scripts/scraper_utils.py`: utilitários compartilhados; verificar se `fetch_nuvemshop_products` retorna campos de specs ou só preço
- `app/models/paddle.py`: `validation_sources` (List[str]) já existe — usar para registrar fonte das specs
- `.github/workflows/quality-audit.yml`: matrix de 10 scrapers com `continue-on-error: true` — template para o novo workflow

### Established Patterns
- Scrapers escrevem direto no DB via `ingest_rows(rows, store_id, session)` — enriquecedor deve seguir padrão similar com `update_paddle_specs(paddle_id, specs, session)`
- `FaceMaterial` e `PaddleShape` são enums no modelo — enriquecedor precisa mapear strings dos sites para os valores dos enums
- `validation_sources` já é atualizado pelo `EnrichmentService` — manter esse padrão para rastreabilidade

### Integration Points
- `paddle_master` atualizado diretamente pelo enriquecedor após match por `brand_name` + `model_name`
- Novo workflow semanal: step 1 = rodar 10 scrapers de preço (ou apenas enriquecedor, se desacoplado), step 2 = rodar quality audit
- `quality-audit.yml` roda a cada hora — o novo workflow semanal é adicional, não substituto

</code_context>

<specifics>
## Specific Ideas

- Foco total em qualidade sobre cobertura: melhor 60% de paddles com specs perfeitas do que 80% com specs duvidosas
- Catálogo começa do zero com dados de scraping BR — sem herança de dados americanos

</specifics>

<deferred>
## Deferred Ideas

- Retry logic nos scrapers de preço — mencionado como pendente desde v2.0, mas fora do escopo desta fase
- Alertas (Telegram/GitHub Issue) quando taxa de scraping de specs cai — pode ser adicionado no Phase 13+ ou como melhoria do workflow

</deferred>

---

*Phase: 12-spec-enrichment-scrapers*
*Context gathered: 2026-03-21*
