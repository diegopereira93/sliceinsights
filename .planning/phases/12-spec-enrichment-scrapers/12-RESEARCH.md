# Phase 12: Spec Enrichment Scrapers - Research

**Researched:** 2026-03-21
**Domain:** Python web scraping (requests/BS4 + Playwright), SQLModel, GitHub Actions
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Specs válidas **somente** se extraídas das páginas das lojas brasileiras
- `enrichment.py` será **arquivado** — catálogo começa do zero com dados 100% provenientes do scraping BR
- Enriquecer um paddle **somente** se os 4 campos estiverem presentes: `core_thickness_mm`, `face_material`, `weight_grams`, `shape`
- Specs parciais (1-3 campos) não são salvas neste ciclo — produto permanece sem specs
- Falha de scraper = exceção Python não capturada; specs vazias/incompletas são resultado válido, não falha
- Workflow: `continue-on-error: true` por scraper — falha em uma loja não bloqueia as demais
- `scrape_product_specs.py` evolui para cobrir as 10 lojas — torna-se o enriquecedor central
- Claude analisa cada site e decide entre `requests`/BeautifulSoup ou Playwright per-loja
- Persistência diretamente no `paddle_master` via SQLModel session (sem JSON intermediário)
- Fonte dos dados registrada em `validation_sources` (ex: `scraping_joola`, `scraping_prospin`)
- Dados de lojas BR têm prioridade absoluta: sobrescrever qualquer valor anterior quando os 4 campos são encontrados
- Após ciclo completo de enriquecimento, o workflow dispara o quality audit para medir impacto
- Weekly cron é workflow **separado** de `quality-audit.yml`

### Claude's Discretion
- Estratégia exata de HTML parsing por loja (seletores CSS, regex, JSON-LD, etc.)
- Ordem e lógica de fallback entre extração estruturada e texto livre
- Normalização de valores (ex: "16mm" → `16.0`, "Carbon Fiber" → `FaceMaterial.carbon`)
- Mapeamento de campos encontrados nas páginas para os enums `FaceMaterial` e `PaddleShape`
- Estrutura do job de quality audit no novo workflow (steps, paralelismo)

### Deferred Ideas (OUT OF SCOPE)
- Retry logic nos scrapers de preço
- Alertas (Telegram/GitHub Issue) quando taxa de scraping de specs cai
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCRP-02 | Os 10 scrapers de lojas especializadas executam via cron semanal | GitHub Actions weekly schedule pattern identified; quality-audit.yml as template |
| SCRP-03 | Cada scraper captura espessura do núcleo (mm) para cada produto | `extract_mm()` already exists in scrape_product_specs.py; needs per-store CSS selectors |
| SCRP-04 | Cada scraper captura material da superfície para cada produto | `map_face_material()` + `FACE_MATERIAL_MAP` already in scrape_product_specs.py; enum values confirmed |
| SCRP-05 | Cada scraper captura peso (gramas) e formato onde disponível | `extract_weight_g()`, `map_shape()`, `SHAPE_MAP` already exist; `weight_grams` field name inconsistency to fix |
| SCRP-06 | Completude de specs do paddle_master sobe de 0% para ≥70% após ciclo completo | Gate: all 4 fields present before write; quality audit runs post-enrichment cycle |
</phase_requirements>

---

## Summary

Phase 12 evolves the existing `scrape_product_specs.py` (currently covers only 2 stores: Joola + BPS) into a comprehensive enricher covering all 10 BR stores. The core infrastructure — normalization maps, regex extractors, Playwright async scaffolding, and the PaddleMaster model with `validation_sources` — already exists. The main work is: (1) adding per-store spec extraction logic for 8 remaining stores, (2) wiring direct DB persistence instead of writing to JSON, (3) archiving `enrichment.py`, and (4) creating a new weekly GitHub Actions workflow.

The critical insight is the **field name inconsistency**: the existing scraper uses `weight_g` internally, but the CONTEXT.md and requirements use `weight_grams`. The PaddleMaster model does not have a `weight_grams` column — it has `shape` (PaddleShape enum) but NOT `weight_grams` directly on the model. This needs clarification before implementation. The 4-field gate (`core_thickness_mm`, `face_material`, `weight_grams`, `shape`) maps to actual model columns `core_thickness_mm`, `face_material`, `shape` — but `weight_grams` may need to be added, or the CONTEXT.md uses it as a logical field name for weight captured from product pages (to be stored elsewhere or requiring a model migration).

**Primary recommendation:** Evolve `scrape_product_specs.py` into a full 10-store enricher with direct SQLModel persistence. Archive `enrichment.py`. Create `scrape-enrichment.yml` workflow with weekly cron + post-run quality audit step.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| playwright (async_api) | already in requirements | JS-heavy sites (Joola, BPS, Drop Shot, JustPaddles) | Already used in scrape_product_specs.py and scraper_utils.py |
| requests | already in requirements | Static/API-backed sites (Shopify, WooCommerce listing pages) | Already used across all price scrapers |
| beautifulsoup4 | already in requirements | HTML parsing for static product pages | Already used in scraper_utils.py |
| sqlmodel | already in requirements | Direct paddle_master persistence | Existing pattern across all scrapers |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| re (stdlib) | stdlib | Regex extraction of mm/g values | Fallback free-text parsing |
| asyncio (stdlib) | stdlib | Async Playwright orchestration | Any Playwright scraper |

No new dependencies required — all tools are already present.

---

## Architecture Patterns

### Per-Store Technology Map

Based on reading all 10 existing price scrapers:

| Store | Price Scraper Tech | Spec Scraper Approach | Reason |
|-------|-------------------|-----------------------|--------|
| joola (joola.com.br) | Shopify API | Playwright — click "Especificação" tab, `.metafield-row` | Tab-gated structured data; already implemented |
| brazil_pickleball_store (brazilpickleballstore.com.br) | Nuvemshop HTML | Playwright — `.user-content` free text regex | Already implemented |
| yosports (yosports.com.br) | Shopify API | requests/BS4 — Shopify product JSON `body_html` | Shopify stores expose HTML description; JSON-LD or metafields may have specs |
| supremo (lojasupremo.com.br) | HTML (Nuvemshop `.js-item-product`) | requests/BS4 — product page description | Static Nuvemshop; product pages likely have spec tables |
| shark (sharkbeachtennis.com.br) | WooCommerce HTML | requests/BS4 — WooCommerce product page `.woocommerce-product-details__short-description` or tabs | WooCommerce product pages have standard spec tab patterns |
| prospin (prospin.com.br) | WooCommerce HTML | requests/BS4 — WooCommerce product page description | Same as Shark |
| drop_shot_brasil (dropshot.com.br) | Playwright dynamic (`.product-link`) | Playwright — already using dynamic scraper, product page needed | JS-heavy store |
| just_paddles | Playwright async | Playwright — already has full Playwright implementation in `scrape_justpaddles.py` | Already scraping swing/twist weight; extend to the 4 required fields |
| pcklhouse (pcklhouse.com.br) | Nuvemshop HTML | requests/BS4 — product page description | Nuvemshop static |
| propadel (lojapropadel.com.br) | HTML (custom BS4) | requests/BS4 — product page description | Already custom BS4 scraper |

### Recommended Project Structure

The enricher becomes a standalone step, not merged into price scrapers:

```
scripts/
├── scrape_product_specs.py    # EVOLVE: 2 stores → 10 stores, JSON → direct DB
├── scrape_*.py                # UNCHANGED: price scrapers stay focused on price fields
app/
├── services/
│   └── enrichment.py          # ARCHIVE: move to app/services/_archived/enrichment.py
.github/workflows/
├── quality-audit.yml          # UNCHANGED: hourly audit
└── scrape-enrichment.yml      # NEW: weekly cron — 10 enrichers + quality audit
```

### Pattern 1: Direct DB Persistence (replaces JSON output)

The current `scrape_product_specs.py` writes to `app/data/scraped_product_specs.json`. This must be replaced with direct SQLModel writes.

```python
# Match paddle by brand_name + model_name (existing pattern from ingestor.py)
from sqlmodel import Session, select
from app.models.paddle import PaddleMaster
from app.models.brand import Brand
from app.models.enums import FaceMaterial, PaddleShape

def update_paddle_specs(specs: dict, session: Session) -> bool:
    """
    Write specs to paddle_master if all 4 required fields are present.
    Returns True if paddle was updated, False if skipped.
    """
    required = ['core_thickness_mm', 'face_material', 'weight_grams', 'shape']
    if not all(specs.get(f) is not None for f in required):
        return False  # Partial specs — valid result, not a failure

    brand = session.exec(
        select(Brand).where(Brand.name == specs['brand_name'])
    ).first()
    if not brand:
        return False

    paddle = session.exec(
        select(PaddleMaster).where(
            PaddleMaster.brand_id == brand.id,
            PaddleMaster.model_name == specs['model_name'],
        )
    ).first()
    if not paddle:
        return False

    # Overwrite any previous values (BR data has absolute priority)
    paddle.core_thickness_mm = specs['core_thickness_mm']
    paddle.face_material = FaceMaterial(specs['face_material'].lower())
    paddle.shape = PaddleShape(specs['shape'].lower())
    # weight_grams: see Open Questions — may need model field or separate handling

    source_key = f"scraping_{specs['store_slug']}"
    sources = list(paddle.validation_sources or [])
    if source_key not in sources:
        sources.append(source_key)
    paddle.validation_sources = sources
    paddle.specs_source = "scraping"

    session.add(paddle)
    return True
```

### Pattern 2: Weekly GitHub Actions Workflow

Template based on `quality-audit.yml` (already read):

```yaml
# .github/workflows/scrape-enrichment.yml
name: Weekly Spec Enrichment

on:
  schedule:
    - cron: '0 6 * * 1'  # Every Monday at 06:00 UTC
  workflow_dispatch: {}

jobs:
  enrich:
    name: Enrich Specs (${{ matrix.store }})
    runs-on: ubuntu-latest
    continue-on-error: true       # Failure in one store does not block others
    strategy:
      fail-fast: false
      matrix:
        store:
          - joola
          - brazil_pickleball_store
          - yosports
          - supremo
          - shark
          - prospin
          - drop_shot_brasil
          - just_paddles
          - pcklhouse
          - propadel
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: playwright install chromium --with-deps
      - name: Enrich specs for ${{ matrix.store }}
        run: python scripts/scrape_product_specs.py --store ${{ matrix.store }}
        env:
          DATABASE_URL_SYNC: ${{ secrets.DATABASE_URL_SYNC }}

  audit:
    name: Quality Audit Post-Enrichment
    needs: enrich
    if: always()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: python scripts/quality_aggregator.py --consolidate
        env:
          DATABASE_URL_SYNC: ${{ secrets.DATABASE_URL_SYNC }}
          GITHUB_RUN_ID: ${{ github.run_id }}
```

**Key difference from quality-audit.yml:** The enrichment workflow also installs Playwright (`playwright install chromium --with-deps`) since several stores require it.

### Pattern 3: Structured + Freetext Fallback

The existing strategy is correct — implement per store:

1. **Structured first**: look for spec tables, JSON-LD (`<script type="application/ld+json">`), Shopify metafields (`.metafield-row`), WooCommerce attribute tables (`table.woocommerce-product-attributes`)
2. **Free text fallback**: regex on product description body if structured data absent
3. **Validation gate**: only save if all 4 fields found

### Pattern 4: Shopify API as Spec Source

For Joola and yoSports (Shopify stores), the `/products.json` API already used by price scrapers returns `body_html`. This HTML often contains spec tables parseable with BS4 — potentially faster than Playwright for spec extraction. However, Joola's specs are behind a tab requiring JS interaction, so Playwright remains necessary for Joola. YoSports should be tested with BS4 on `body_html` first.

### Anti-Patterns to Avoid

- **Writing to JSON then re-reading**: current scrape_product_specs.py writes JSON; Phase 12 eliminates this intermediate step
- **Merging enrichment into price scrapers**: keep separate as decided in CONTEXT.md
- **One technology for all stores**: Joola and Drop Shot require Playwright; static stores should use requests/BS4 for speed
- **Raising exceptions for empty specs**: empty specs = valid result; only raise on network errors or parse failures that are unexpected
- **Using enrichment.py as a spec source**: archive it, do not call it

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async browser automation | Custom HTTP + JS execution | Playwright (`async_playwright`) | Already in requirements; handles JS rendering, WAF, tabs |
| HTML parsing | String manipulation | BeautifulSoup `soup.select()` | Already in requirements; handles malformed HTML |
| Enum validation | Custom string check | `FaceMaterial(value.lower())` / `PaddleShape(value.lower())` | SQLModel enforces valid enum values at DB write |
| DB session management | Manual connection | `with Session(sync_engine) as session: ... session.commit()` | Existing pattern across all scrapers |
| Pass rate calculation | Custom counter | quality_aggregator.py `--consolidate` | Existing tool; run post-enrichment in workflow |

---

## Common Pitfalls

### Pitfall 1: `weight_grams` Field Does Not Exist on PaddleMaster

**What goes wrong:** CONTEXT.md and REQUIREMENTS.md use `weight_grams` as one of the 4 required fields, but `PaddleMaster` model (paddle.py) has no `weight_grams` column. The existing scraper uses `weight_g` internally as a dict key only.

**Why it happens:** The spec extraction script uses `weight_g` as a temporary key; the model never stored it.

**How to avoid:** Either (a) add `weight_grams: Optional[float]` column to PaddleMaster via Alembic migration, or (b) map `weight_grams` to an existing field. This is the **single blocking unknown** for this phase — must be resolved in Wave 0 / first plan.

**Warning signs:** `AttributeError: 'PaddleMaster' object has no attribute 'weight_grams'` at write time.

### Pitfall 2: Playwright Not Installed in GitHub Actions

**What goes wrong:** `playwright install` is not in quality-audit.yml (it only uses `pip install -r requirements.txt`), so if enrichment workflow copies that template without adding `playwright install chromium --with-deps`, Playwright-based scrapers fail silently or with a cryptic error.

**How to avoid:** Explicitly add `playwright install chromium --with-deps` step before enrichment jobs that need it (joola, brazil_pickleball_store, drop_shot_brasil, just_paddles).

**Warning signs:** `BrowserType.launch: Executable doesn't exist at /home/runner/.cache/ms-playwright/...`

### Pitfall 3: Match by brand_name + model_name Requires Exact Normalization

**What goes wrong:** Ingestor normalizes brand/model with `.title()` and `re.sub(r"\s+", " ", ...)`. If the enricher queries with a different format (e.g., `"JOOLA"` vs `"Joola"`), the paddle won't be found and specs are silently dropped.

**How to avoid:** Reuse `normalize()` from `app/db/ingestor.py` when looking up paddles in `update_paddle_specs()`. The enricher must use the same normalization as the ingestor.

**Warning signs:** 0 paddles updated despite successful scraping.

### Pitfall 4: Shopify API body_html Contains Escaped HTML

**What goes wrong:** For Shopify stores, `body_html` in `/products.json` is HTML-escaped (e.g., `&lt;table&gt;`). Parsing with BS4 directly works, but attempting regex on the raw JSON string before parsing will fail.

**How to avoid:** Always pass `body_html` through `BeautifulSoup(body_html, "html.parser")` before applying selectors or regex.

### Pitfall 5: specs_confidence Field Semantic

**What goes wrong:** `PaddleMaster.specs_confidence` defaults to `1.0` for new paddles (not `0` as the existing `scrape_product_specs.py` filters on). The current enricher queries `.where(PaddleMaster.specs_confidence == 0)` — this may miss paddles that already have confidence 1.0 from previous (incorrect) data.

**How to avoid:** For Phase 12's purpose (enriching from BR scraping), the enricher should query all paddles with `MarketOffer` URLs from BR stores, regardless of current `specs_confidence`. The 4-field gate ensures quality; overwriting is intentional per CONTEXT.md.

---

## Code Examples

### Enum Mapping (verified from enums.py)

```python
# FaceMaterial valid values: "carbon", "fiberglass", "hybrid", "kevlar"
# PaddleShape valid values: "standard", "elongated", "widebody"

from app.models.enums import FaceMaterial, PaddleShape

face = FaceMaterial("carbon")      # FaceMaterial.CARBON
shape = PaddleShape("elongated")   # PaddleShape.ELONGATED
```

The existing `FACE_MATERIAL_MAP` in scrape_product_specs.py correctly maps to uppercase strings (`"CARBON"`, `"FIBERGLASS"`, etc.) but the enum constructor expects lowercase values (`"carbon"`). The mapping layer must do `.lower()` before constructing the enum.

### Existing Extractors (verified from scrape_product_specs.py)

```python
# Already implemented — reuse directly:
extract_mm(text)           # "16mm" → 16.0, valid range 10-20 enforced in parse_freetext
extract_weight_g(text)     # "226.8g" or "226,8 gramas" → 226.8
map_face_material(text)    # "carbono" → "CARBON"
map_shape(text)            # "elongada" → "ELONGATED"
parse_freetext_specs(text) # Combined extractor for unstructured text
```

### WooCommerce Spec Table Pattern (BS4)

```python
# WooCommerce product pages often expose specs in:
# table.woocommerce-product-attributes td.woocommerce-product-attributes-item__value
from bs4 import BeautifulSoup
import requests

r = requests.get(product_url, headers=HEADERS, timeout=15)
soup = BeautifulSoup(r.text, "html.parser")
rows = soup.select("table.woocommerce-product-attributes tr")
for row in rows:
    label = row.select_one("th")
    value = row.select_one("td")
    if label and value:
        process_spec_field(label.get_text(strip=True), value.get_text(strip=True))
```

### Nuvemshop Product Page (BS4)

```python
# Nuvemshop product page description: div.product-description or .js-product-description
soup = BeautifulSoup(r.text, "html.parser")
desc_el = soup.select_one(".product-description, .js-product-description, [itemprop='description']")
if desc_el:
    text = desc_el.get_text(separator="\n", strip=True)
    specs = parse_freetext_specs(text)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| enrichment.py — fuzzy match on US paddle_stats_dump.csv | scrape_product_specs.py — live scraping of BR store pages | Phase 12 | Specs now 100% from verified BR sources |
| JSON intermediate file output | Direct SQLModel session writes | Phase 12 | Eliminates JSON artifact, atomic per-paddle update |
| 2 stores covered (Joola, BPS) | 10 stores covered | Phase 12 | Full BR catalog coverage |
| No weekly automation | New `scrape-enrichment.yml` weekly workflow | Phase 12 | Automatic spec refresh |

---

## Open Questions

1. **`weight_grams` field on PaddleMaster model**
   - What we know: The model does not have a `weight_grams` column (verified from paddle.py). CONTEXT.md lists it as a required field for the 4-field gate.
   - What's unclear: Is this a new column requiring an Alembic migration, or is it stored differently (e.g., embedded in a JSON field, or implicitly the grams value stored elsewhere)?
   - Recommendation: **Wave 0 task must add `weight_grams: Optional[float]` to PaddleMaster** via Alembic migration. This is blocking — cannot save specs without resolving this.

2. **specs_confidence initial value = 1.0 vs 0**
   - What we know: `PaddleMaster.specs_confidence` defaults to `1.0`. Current `scrape_product_specs.py` queries paddles where `specs_confidence == 0` to find unenriched paddles.
   - What's unclear: After Phase 11 seed cleanup, what is the actual `specs_confidence` of freshly ingested paddles?
   - Recommendation: Query all paddles with active BR market offers, not filtered by `specs_confidence`. Or, if Phase 11 sets `specs_confidence = 0` for scraped paddles, the existing filter is correct.

3. **Playwright in GitHub Actions — install scope**
   - What we know: `quality-audit.yml` does not install Playwright. The enrichment workflow needs it.
   - What's unclear: Whether to install Playwright for all 10 matrix jobs (simpler) or only the 4 that need it (faster).
   - Recommendation: Install for all matrix jobs for simplicity; overhead is ~30 seconds per job and avoids conditional logic.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (inferred from project structure) |
| Config file | None detected — check pyproject.toml or pytest.ini |
| Quick run command | `pytest scripts/ -x -q` |
| Full suite command | `pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCRP-02 | Workflow YAML has correct weekly schedule and 10-store matrix | manual | Validate YAML structure | ❌ Wave 0 |
| SCRP-03 | `extract_mm()` correctly parses "16mm", "16,0mm", edge cases | unit | `pytest tests/test_spec_enricher.py::test_extract_mm -x` | ❌ Wave 0 |
| SCRP-04 | `map_face_material()` maps all PT-BR/EN variants to correct enum | unit | `pytest tests/test_spec_enricher.py::test_face_material_map -x` | ❌ Wave 0 |
| SCRP-05 | `extract_weight_g()` + `map_shape()` parse correctly | unit | `pytest tests/test_spec_enricher.py::test_weight_shape -x` | ❌ Wave 0 |
| SCRP-06 | 4-field gate: partial specs not saved; complete specs saved | unit | `pytest tests/test_spec_enricher.py::test_four_field_gate -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_spec_enricher.py -x -q`
- **Per wave merge:** `pytest -x -q`
- **Phase gate:** Full suite green + manual verification of spec completeness in DB

### Wave 0 Gaps

- [ ] `tests/test_spec_enricher.py` — unit tests for extractors and 4-field gate (SCRP-03, SCRP-04, SCRP-05, SCRP-06)
- [ ] Alembic migration for `weight_grams` field on PaddleMaster (SCRP-05, blocking)
- [ ] Confirm pytest is installed: `pip show pytest`

---

## Sources

### Primary (HIGH confidence)
- `scripts/scrape_product_specs.py` — Current implementation, extractors, maps, Playwright pattern
- `app/models/paddle.py` — PaddleMaster fields, `validation_sources`, `specs_confidence`, `FaceMaterial`, `PaddleShape` enums
- `app/models/enums.py` — Exact enum values for FaceMaterial and PaddleShape
- `app/db/ingestor.py` — `ingest_rows()` contract, `normalize()` function, session pattern
- `.github/workflows/quality-audit.yml` — Matrix + `continue-on-error` template
- `scripts/scraper_utils.py` — `fetch_nuvemshop_products`, `fetch_woocommerce_products`, `fetch_shopify_products`, `fetch_dynamic_products`
- All 10 `scripts/scrape_*.py` files — Store technology identification

### Secondary (MEDIUM confidence)
- CONTEXT.md — User decisions (locked and discretionary)
- REQUIREMENTS.md — SCRP-02 through SCRP-06

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in project, verified from source
- Architecture: HIGH — based on direct code reading, not assumptions
- Per-store tech map: MEDIUM — based on price scraper tech; actual spec page structure requires live testing per store
- Pitfalls: HIGH for field name issues (verified from model); MEDIUM for per-store gotchas

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (store HTML structures may change)
