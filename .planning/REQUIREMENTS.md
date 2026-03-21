# Requirements: SliceInsights — v3.0 Catálogo Confiável Brasileiro

**Defined:** 2026-03-20
**Core Value:** Todo dado que flui para as recomendações deve ser confiável — vendido no Brasil, com specs verificadas via scraping.

## v3 Requirements

### Scraping — Lojas Especializadas

- [ ] **SCRP-01**: Sistema remove todos os CSVs de seed (`app/data/`, `data/raw/`) e opera 100% via scraping
- [ ] **SCRP-02**: Os 10 scrapers de lojas especializadas (brazil_pickleball_store, joola, yosports, supremo, shark, prospin, drop_shot_brasil, just_paddles, pcklhouse, propadel) executam via cron semanal
- [ ] **SCRP-03**: Cada scraper captura espessura do núcleo (mm) para cada produto
- [ ] **SCRP-04**: Cada scraper captura material da superfície (carbono cru, fibra de vidro, híbrido, Kevlar) para cada produto
- [ ] **SCRP-05**: Cada scraper captura peso (gramas) e formato (padrão, alongado) onde disponível
- [ ] **SCRP-06**: Completude de specs do paddle_master sobe de 0% para ≥ 70% após ciclo de scraping completo

### Store — Catálogo de Lojas

- [ ] **STORE-01**: Sistema mantém catálogo de lojas especializadas com nome, URL base, status ativo e marcas disponíveis
- [ ] **STORE-02**: Cada oferta de mercado está associada à sua loja de origem com URL direta do produto
- [ ] **STORE-03**: API retorna lista de lojas com metadados e filtro por marca disponível

### Catalog — API de Catálogo

- [ ] **CAT-01**: Usuário pode listar todas as raquetes disponíveis no Brasil via endpoint da API
- [ ] **CAT-02**: Usuário pode filtrar raquetes por espessura do núcleo (ex: 13mm, 16mm, 19mm)
- [ ] **CAT-03**: Usuário pode filtrar raquetes por material da superfície
- [ ] **CAT-04**: Usuário pode filtrar raquetes por faixa de preço (R$)
- [ ] **CAT-05**: Usuário pode filtrar raquetes por marca e por loja
- [ ] **CAT-06**: Cada raquete retornada pela API inclui URL da loja brasileira onde pode ser comprada

### Web — Página de Catálogo

- [ ] **WEB-01**: Usuário acessa página web de catálogo com listagem de raquetes
- [ ] **WEB-02**: Página exibe filtros laterais (espessura, material, preço, marca, loja)
- [ ] **WEB-03**: Página atualiza listagem dinamicamente ao aplicar filtros

### Recommend — Assistente de IA

- [ ] **REC-01**: Assistente de IA recebe perfil do jogador (nível de jogo, estilo, orçamento) e retorna raquetes recomendadas do catálogo
- [ ] **REC-02**: Cada recomendação inclui justificativa técnica (ex: "núcleo 16mm para equilíbrio potência/controle") e link de compra no Brasil
- [ ] **REC-03**: Assistente consulta catálogo em tempo real (não depende de dados estáticos)

## v4 Requirements (Deferred)

### Qualidade

- **QUAL-01**: Retry logic nos scrapers (atualmente todos usam `except Exception` sem recuperação)
- **QUAL-02**: Detecção de anomalia com ML nos dados de qualidade

### Expansão

- **EXP-01**: Catálogo de marcas com entidades (Selkirk, JOOLA, Diadem, etc.) e histórico de modelos por série

## Out of Scope

| Feature | Reason |
|---------|--------|
| Seed CSVs | Eliminados — catálogo deve ser sempre derivado de scraping confiável |
| Raquetes fora do Brasil | Foco no mercado brasileiro; importação direta sem garantia local excluída |
| Catálogo de marcas (entidade separada) | Valor menor vs. complexidade; marcas como atributo de produto é suficiente para v3 |
| Streaming em tempo real | Pipeline batch semanal suficiente para catálogo de raquetes |
| ML de anomalia | Infraestrutura de qualidade (v2) precisa estabilizar antes de ML |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCRP-01 | Phase 11 | Pending |
| SCRP-02 | Phase 12 | Pending |
| SCRP-03 | Phase 12 | Pending |
| SCRP-04 | Phase 12 | Pending |
| SCRP-05 | Phase 12 | Pending |
| SCRP-06 | Phase 12 | Pending |
| STORE-01 | Phase 11 | Pending |
| STORE-02 | Phase 11 | Pending |
| STORE-03 | Phase 13 | Pending |
| CAT-01 | Phase 13 | Pending |
| CAT-02 | Phase 13 | Pending |
| CAT-03 | Phase 13 | Pending |
| CAT-04 | Phase 13 | Pending |
| CAT-05 | Phase 13 | Pending |
| CAT-06 | Phase 13 | Pending |
| WEB-01 | Phase 14 | Pending |
| WEB-02 | Phase 14 | Pending |
| WEB-03 | Phase 14 | Pending |
| REC-01 | Phase 15 | Pending |
| REC-02 | Phase 15 | Pending |
| REC-03 | Phase 15 | Pending |

**Coverage:**
- v3 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-20*
*Last updated: 2026-03-20 — roadmap created, traceability confirmed*
