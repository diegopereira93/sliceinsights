# Phase 11: Seed Cleanup & Store Catalog - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Remover todos os CSVs de seed e fazer o catálogo operar 100% via scraping. Criar uma tabela `stores` com metadados das 10 lojas especializadas de pickleball no Brasil. Vincular cada `market_offer` à sua loja de origem via FK `store_id`.

Fora do escopo desta fase: enriquecimento de specs técnicas (Phase 12), API de catálogo (Phase 13), front-end (Phase 14), assistente de IA (Phase 15).

</domain>

<decisions>
## Implementation Decisions

### Bootstrap do catálogo de lojas
- Uma migration Alembic cria a tabela `stores` e insere os 10 registros diretamente como data migration (Python list hardcoded na migration)
- Rastreável no git, idempotente, sem dependência de arquivo externo
- As 10 lojas confirmadas (com domínios extraídos dos scrapers existentes):
  1. Brazil Pickleball Store — `www.brazilpickleballstore.com.br`
  2. Joola Brasil — `joola.com.br`
  3. yoSports — `yosports.com.br`
  4. Loja Supremo — `www.lojasupremo.com.br`
  5. Shark — `sharkbeachtennis.com.br`
  6. ProSpin — `www.prospin.com.br`
  7. Drop Shot Brasil — `www.dropshot.com.br`
  8. PCKL House — `www.pcklhouse.com.br`
  9. ProPadel — `www.lojapropadel.com.br`
  10. Just Paddles — `www.justpaddles.com`

### Campos da tabela stores
- `id`, `name`, `base_url`, `is_active` (bool), `available_brands` (lista/JSONB ou texto separado) — conforme STORE-01
- Just Paddles é a única loja sem CSV de seed histórico; as outras 9 têm dados via `store_name` existente

### Vinculação market_offer → store (STORE-02)
- Migration Alembic adiciona coluna `store_id` (FK → `stores.id`) como nullable inicialmente
- Data migration: UPDATE em `market_offers` mapeando os 9 valores de `store_name` existentes para o `store_id` correspondente
- Após mapeamento, tornar `store_id` NOT NULL
- Preservar dados existentes (não fazer clean slate)
- A coluna `url` em `market_offer` já representa a URL direta do produto — manter; avaliar se `store_name` pode ser removida após migration (Claude decide)

### Remoção de seeds e arquitetura do pipeline
- `app/db/seed_brazil_catalog.py` é removido completamente
- Os 10 scrapers (`scrape_*.py`) são adaptados para escrever diretamente no DB (via SQLModel/SQLAlchemy session), sem passar por arquivos CSV intermediários
- `data/raw/` passa a ser debug-only: gitignored para CSVs (manter apenas `.gitkeep`); scrapers podem continuar gerando arquivos como artefato de depuração local, mas o pipeline não os lê
- `app/data/` (CSVs estáticos: `brazil_pickleball_store.csv`, `joola_brazil.csv`, `paddle_stats_dump.csv`, `manual_specs.json`, `scraped_product_specs.json`) — CSVs de ofertas são removidos; verificar se JSONs de specs ainda são necessários antes de deletar

### Filtro de produto: apenas paddles
- Scrapers e ingestão devem descartar acessórios (bags, balls, apparel, etc.)
- Apenas raquetes de pickleball (paddles) entram no `paddle_master` e `market_offers`
- Lógica de filtragem aplicada no momento da ingestão no DB, não no scraper (para manter scrapers simples)

### Segurança dos testes
- Auditar todos os testes existentes que leem de `data/raw/` ou `app/data/` CSVs
- Converter esses testes para usar fixtures de DB (SQLite em memória ou factory functions)
- Adicionar smoke test que confirma: com `data/raw/` vazio, o pipeline roda sem erros
- O success criteria "deletar os CSVs não quebra nenhum teste" deve ser verificado explicitamente antes do merge

### Claude's Discretion
- Schema exato de `available_brands` na tabela `stores` (JSONB array vs. tabela N:M vs. texto separado por vírgula)
- Se manter ou remover a coluna `store_name` em `market_offers` após a migration
- Estratégia de retry/upsert dos scrapers ao escrever no DB (evitar duplicatas)
- Nomeclatura dos métodos de DB session nos scrapers adaptados

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos desta fase
- `.planning/REQUIREMENTS.md` — SCRP-01 (remoção de CSVs), STORE-01 (tabela stores com metadados), STORE-02 (market_offer vinculado à loja com URL direta)
- `.planning/ROADMAP.md` §"Phase 11: Seed Cleanup & Store Catalog" — success criteria e dependências

### Modelos existentes relevantes
- `app/models/market_offer.py` — modelo atual a ser migrado (store_name: str → store_id: FK)
- `app/models/paddle.py` — relação com MarketOffer que precisa ser preservada
- `app/models/brand.py` — Brand model existente (o stores.available_brands deve referenciar)
- `app/models/__init__.py` — onde o novo modelo Store deve ser registrado

### Seed script a ser removido
- `app/db/seed_brazil_catalog.py` — mapeia SOURCES (9 CSVs) para o DB; referência de como o mapeamento store_name funciona hoje

### Scrapers a serem adaptados
- `scripts/scrape_brazil_store.py` — DOMAIN: www.brazilpickleballstore.com.br
- `scripts/scrape_joola.py` — DOMAIN: joola.com.br
- `scripts/scrape_yosports.py` — DOMAIN: yosports.com.br
- `scripts/scrape_supremo.py` — DOMAIN: www.lojasupremo.com.br
- `scripts/scrape_shark.py` — DOMAIN: sharkbeachtennis.com.br
- `scripts/scrape_prospin.py` — DOMAIN: www.prospin.com.br
- `scripts/scrape_dropshot_brasil.py` — URL: www.dropshot.com.br
- `scripts/scrape_pcklhouse.py` — DOMAIN: www.pcklhouse.com.br
- `scripts/scrape_propadel.py` — DOMAIN: www.lojapropadel.com.br
- `scripts/scrape_justpaddles.py` — DOMAIN: www.justpaddles.com (sem CSV histórico)
- `scripts/run_scraper.py` — orquestrador do pipeline; ponto de entrada a ser atualizado
- `scripts/scraper_utils.py` — utilitários compartilhados pelos scrapers

### Migrations existentes (para encadear a nova)
- `alembic/versions/` — chain atual: add_specs_fields, add_validation_sources, add_deploy_versioning, add_quality_metrics, add_slo_logs_table, add_ai_knowledge_base

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/scraper_utils.py` — funções shared (`fetch_shopify_products`, `fetch_nuvemshop_products`, `fetch_woocommerce_products`, `fetch_html_products`, `shopify_product_to_row`): os scrapers adaptados devem usar essas utilidades para a parte HTTP, adicionando apenas a camada de DB write
- `app/db/database.py` — `sync_engine`, `init_db_sync`, `Session`: os scrapers adaptados usarão esses para escrever no DB (mesmo padrão do seed_brazil_catalog.py)
- `app/models/brand.py`, `app/models/paddle.py` — lógica de deduplicação de Brand e PaddleMaster existente no seed_brazil_catalog.py pode ser extraída em helpers reutilizáveis

### Established Patterns
- **Alembic migrations**: todas em `alembic/versions/` como arquivos Python autogenerados; data migrations são feitas com `op.execute()` ou Session dentro da migration
- **SQLModel**: todos os modelos usam SQLModel com `table=True`; novos modelos devem seguir o padrão de `Base/Table/Read/Create` classes separadas
- **Scrapers → CSV hoje**: scrapers escrevem CSV com colunas `[brand_name, model_name, price_brl, product_url, store_name, image_url]`; ao adaptar para DB, essa é a estrutura de dados de entrada para o ingestor

### Integration Points
- Novo modelo `Store` em `app/models/store.py` → registrar em `app/models/__init__.py`
- `MarketOffer.store_id` → FK para `stores.id` (migration)
- `app/main.py` ou startup: garantir que a tabela `stores` é criada antes de qualquer scraper rodar
- `scripts/run_scraper.py` (modificado no branch atual): ponto central onde scrapers são chamados — deve ser atualizado para refletir a nova arquitetura de escrita direta no DB

</code_context>

<specifics>
## Specific Ideas

- "Apenas raquetes de pickleball (paddles) entram no catálogo — acessórios são descartados na ingestão" (decisão explícita do usuário)
- Just Paddles (`www.justpaddles.com`) é loja americana com scrapers buscando por query search, não por categoria — manter essa lógica ao adaptar para escrita no DB
- `data/raw/` deve continuar existindo como diretório (com `.gitkeep`) para não quebrar scrapers que ainda escrevem para debug local; apenas os CSVs não devem ser commitados

</specifics>

<deferred>
## Deferred Ideas

- Nenhuma ideia de escopo fora desta fase foi sugerida — discussão manteve-se dentro dos limites de Phase 11.

</deferred>

---

*Phase: 11-seed-cleanup-store-catalog*
*Context gathered: 2026-03-20*
