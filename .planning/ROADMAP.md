# Roadmap: SliceInsights

## Milestones

- ✅ **v1.0 Data Pipeline Audit** — Phases 1-4 (shipped 2026-03-19)
- ✅ **v2.0 Workflows & Automation** — Phases 5-10 (shipped 2026-03-20)
- 🚧 **v3.0 Catálogo Confiável Brasileiro** — Phases 11-15 (in progress)

## Phases

<details>
<summary>✅ v1.0 Data Pipeline Audit (Phases 1–4) — SHIPPED 2026-03-19</summary>

- [x] Phase 1: Scraper Health Audit (3/3 plans) — completed 2026-03-19
- [x] Phase 2: Data Quality Analysis (2/2 plans) — completed 2026-03-19
- [x] Phase 3: Automation & Reliability Mapping (1/1 plan) — completed 2026-03-19
- [x] Phase 4: Audit Report & Recommendations (3/3 plans) — completed 2026-03-19

Full archive: `.planning/milestones/v1.0-ROADMAP.md`

</details>

<details>
<summary>✅ v2.0 Workflows & Automation (Phases 5–10) — SHIPPED 2026-03-20</summary>

- [x] Phase 5: CI/CD & Testing (3/3 plans) — completed 2026-03-19
- [x] Phase 6: SLO Enforcement & Validation (5/5 plans) — completed 2026-03-20
- [x] Phase 7: Alerts & Monitoring (2/2 plans) — completed 2026-03-19
- [x] Phase 8: Deploy & Release Strategy (3/3 plans) — completed 2026-03-20
- [x] Phase 9: Data Quality Checks & Reporting (3/3 plans) — completed 2026-03-20
- [x] Phase 10: SLO Gate Fix (1/1 plan) — completed 2026-03-20

Full archive: `.planning/milestones/v2.0-ROADMAP.md`

</details>

---

### v3.0 Catálogo Confiável Brasileiro (In Progress)

**Milestone Goal:** Construir um catálogo confiável de raquetes de pickleball vendidas no Brasil — enriquecido com specs técnicas via scraping semanal — entregando valor ao público brasileiro e alimentando o assistente de IA de recomendação.

- [x] **Phase 11: Seed Cleanup & Store Catalog** - Fix remaining issues: migration bug, tracked CSVs, justpaddles market-offer ingestion (completed 2026-03-21)
- [x] **Phase 12: Spec Enrichment Scrapers** - Enrich all 10 scrapers with technical spec extraction; run weekly via new cron (completed 2026-03-21)
- [x] **Phase 13: Catalog API** - REST endpoints to list and filter paddles by specs, store, brand, and price (completed 2026-03-21)
- [x] **Phase 14: Web Catalog Page** - Browser-accessible catalog page with live filter controls (completed 2026-03-21)
- [x] **Phase 15: AI Recommendation Assistant** - Player profile quiz returns personalized paddle recommendations with Brazilian purchase links (completed 2026-03-21)

## Phase Details

### Phase 11: Seed Cleanup & Store Catalog
**Goal**: O catálogo opera 100% via scraping — sem CSVs de seed — e cada loja especializada é um registro gerenciado com metadados
**Depends on**: Phase 10
**Requirements**: SCRP-01, STORE-01, STORE-02
**Success Criteria** (what must be TRUE):
  1. Running the pipeline produces no reads from `app/data/` or `data/raw/` CSV files — all catalog data comes from scraper output
  2. A `stores` table exists with name, base URL, active status, and available brands for each of the 10 specialized stores
  3. Every market offer row in the database has a non-null `store_id` and a direct product URL pointing to the source store
  4. Deleting the seed CSV files does not break the application or any existing test
**Plans:** 3/2 plans complete
Plans:
- [ ] 11-01-PLAN.md — Fix migration bulk_insert bug + untrack seed CSVs from data/raw/
- [ ] 11-02-PLAN.md — Add market-offer ingestion to scrape_justpaddles.py + test

### Phase 12: Spec Enrichment Scrapers
**Goal**: Os 10 scrapers capturam specs técnicas completas e executam semanalmente via cron — elevando a completude de specs de 0% para ≥ 70%
**Depends on**: Phase 11
**Requirements**: SCRP-02, SCRP-03, SCRP-04, SCRP-05, SCRP-06
**Success Criteria** (what must be TRUE):
  1. Each of the 10 scraper modules returns `core_thickness_mm`, `surface_material`, `weight_grams`, and `shape` fields alongside price data
  2. A new GitHub Actions workflow (separate from `quality-audit.yml`) triggers all 10 scrapers on a weekly schedule
  3. After one full scraping cycle, `paddle_master` spec completeness is ≥ 70% as measured by the existing quality audit tool
  4. The weekly cron completes without error for at least 8 of the 10 stores (80% pass rate)
**Plans:** 3/3 plans complete
Plans:
- [ ] 12-01-PLAN.md — Foundation: weight_grams migration, enricher core with 4-field gate + DB persistence, tests, archive enrichment.py
- [ ] 12-02-PLAN.md — Add 8 remaining store extractors (BS4 + Playwright) to scrape_product_specs.py
- [ ] 12-03-PLAN.md — Create weekly scrape-enrichment.yml GitHub Actions workflow

### Phase 13: Catalog API
**Goal**: Usuários e o assistente de IA podem consultar o catálogo completo de raquetes com filtros por specs, marca, loja e preço
**Depends on**: Phase 12
**Requirements**: STORE-03, CAT-01, CAT-02, CAT-03, CAT-04, CAT-05, CAT-06
**Success Criteria** (what must be TRUE):
  1. `GET /catalog/paddles` returns all available paddles in Brazil with a store purchase URL in each record
  2. Query parameters `core_thickness`, `surface_material`, `price_min`, `price_max`, `brand`, and `store` each filter results correctly
  3. `GET /catalog/stores` returns all 10 stores with metadata and supports filtering by available brand
  4. All catalog endpoints return an empty list (not an error) when no matching paddles exist
**Plans**: 2 plans
Plans:
- [x] 13-01-PLAN.md — Store slug migration + catalog endpoints (paddles + stores) + router wiring
- [ ] 13-02-PLAN.md — Comprehensive test suite for all catalog requirements

### Phase 14: Web Catalog Page
**Goal**: Qualquer pessoa pode navegar e filtrar o catálogo de raquetes disponíveis no Brasil via página web
**Depends on**: Phase 13
**Requirements**: WEB-01, WEB-02, WEB-03
**Success Criteria** (what must be TRUE):
  1. A user can open the catalog page in a browser and see a listing of paddles with no additional setup
  2. The page displays filter controls for core thickness, surface material, price range, brand, and store
  3. Applying a filter updates the paddle listing to show only matching results
  4. Each paddle card includes a clickable link to the Brazilian store where it can be purchased
**Plans**: 3 plans
Plans:
- [x] 14-01-PLAN.md — Types, backend image_url fix, and presentational components (card, grid, skeleton, pagination)
- [x] 14-02-PLAN.md — FilterDrawer extension, CatalogClient, SSR page, bottom-nav wiring
- [ ] 14-03-PLAN.md — Build verification and human checkpoint

### Phase 15: AI Recommendation Assistant
**Goal**: Jogadores recebem recomendações personalizadas de raquetes com justificativa técnica e link de compra no Brasil
**Depends on**: Phase 14
**Requirements**: REC-01, REC-02, REC-03
**Success Criteria** (what must be TRUE):
  1. Submitting a player profile (skill level, play style, budget) returns at least one paddle recommendation drawn from the live catalog
  2. Each recommendation includes a plain-language technical justification referencing spec attributes (e.g., "nucleo 16mm para equilibrio potencia/controle")
  3. Each recommendation includes a direct purchase link to a Brazilian store
  4. When no catalog paddle matches the submitted profile, the assistant returns a meaningful "no match" message rather than an empty response or error
**Plans**: 3 plans
Plans:
- [x] 15-01-PLAN.md — Backend: schema extension (MarketOfferOut, image_url) + /recommend and /recommend/chat endpoints + tests
- [x] 15-02-PLAN.md — Frontend: TypeScript types + wizard page + result cards + chat panel + catalog CTA
- [x] 15-03-PLAN.md — Build verification and human checkpoint

## Progress

**Execution Order:** 11 → 12 → 13 → 14 → 15

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Scraper Health Audit | v1.0 | 3/3 | ✅ Complete | 2026-03-19 |
| 2. Data Quality Analysis | v1.0 | 2/2 | ✅ Complete | 2026-03-19 |
| 3. Automation & Reliability Mapping | v1.0 | 1/1 | ✅ Complete | 2026-03-19 |
| 4. Audit Report & Recommendations | v1.0 | 3/3 | ✅ Complete | 2026-03-19 |
| 5. CI/CD & Testing | v2.0 | 3/3 | ✅ Complete | 2026-03-19 |
| 6. SLO Enforcement & Validation | v2.0 | 5/5 | ✅ Complete | 2026-03-20 |
| 7. Alerts & Monitoring | v2.0 | 2/2 | ✅ Complete | 2026-03-19 |
| 8. Deploy & Release Strategy | v2.0 | 3/3 | ✅ Complete | 2026-03-20 |
| 9. Data Quality Checks & Reporting | v2.0 | 3/3 | ✅ Complete | 2026-03-20 |
| 10. SLO Gate Fix | v2.0 | 1/1 | ✅ Complete | 2026-03-20 |
| 11. Seed Cleanup & Store Catalog | v3.0 | Complete | ✅ Complete | 2026-03-21 |
| 12. Spec Enrichment Scrapers | v3.0 | 3/3 | ✅ Complete | 2026-03-21 |
| 13. Catalog API | 2/2 | Complete    | ✅ Complete | 2026-03-21 |
| 14. Web Catalog Page | v3.0 | Complete | ✅ Complete   | 2026-03-21 |
| 15. AI Recommendation Assistant | v3.0 | 3/3 | Complete   | 2026-03-21 |

### Phase 15.1: Remover pagina de catalogo, pois ja existe na home com melhores filtros (INSERTED)

**Goal:** Remover rota /catalog e todos os artefatos exclusivos, substituir nav por /recommend, adicionar redirect 301
**Requirements**: CLEANUP-01, CLEANUP-02, CLEANUP-03, CLEANUP-04, CLEANUP-05
**Depends on:** Phase 15
**Plans:** 1 plan

Plans:
- [ ] 15.1-01-PLAN.md — Deletar rota /catalog, componentes catalog/, types/catalog.ts, atualizar bottom-nav para /recommend, limpar FilterDrawer props orfas, adicionar redirect 301
