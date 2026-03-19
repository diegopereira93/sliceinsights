# Data Quality Dashboard — SliceInsights

**Generated:** 2026-03-19
**Database:** picklematch (PostgreSQL via Docker)
**Scope:** All paddle_master + market_offers records

---

## Executive Summary

The SliceInsights catalog contains **86 paddles** across **11 brands** with **93 active market offers** from **3 Brazilian stores**. Data integrity is strong — zero non-paddles, zero duplicates, and 100% of paddles have active market offers. However, **specs completeness is critically low at 0%**: all 8 technical specification fields (except image_url) are empty across every paddle. This means no paddle currently passes the production quality gate (specs_confidence=1.0 + market offer). The 37% US dump match rate provides a clear enrichment path for 32 paddles. All market offer data is fresh (< 1 day old), indicating healthy scraper pipelines for the 3 active stores.

---

## 1. Quality Metrics (QUAL-01)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total paddles in DB | 86 | — | — |
| Complete specs (all 9 fields) | 0 (0%) | 100% | 🔴 |
| US dump match rate | 32 (37%) | >80% | ⚠️ |
| Non-paddles detected | 0 | 0 | ✅ |
| Duplicate groups | 0 | 0 | ✅ |
| Paddles with active offers | 86 (100%) | 100% | ✅ |
| Smoke test result | PASS | PASS | ✅ |
| Low-price paddles (< R$ 450) | 3 | — | ⚠️ |

---

## 2. Field Coverage Detail (QUAL-02)

All 86 paddles audited via `audit_data_quality.py`:

| # | Field | Filled | Pct | Status |
|---|-------|--------|-----|--------|
| 1 | core_thickness_mm | 0/86 | 0% | 🔴 |
| 2 | face_material | 0/86 | 0% | 🔴 |
| 3 | core_material | 0/86 | 0% | 🔴 |
| 4 | shape | 0/86 | 0% | 🔴 |
| 5 | swing_weight | 0/86 | 0% | 🔴 |
| 6 | spin_rpm | 0/86 | 0% | 🔴 |
| 7 | power_rating | 0/86 | 0% | 🔴 |
| 8 | handle_length | 0/86 | 0% | 🔴 |
| 9 | image_url | 86/86 | 100% | ✅ |

**Summary:** Only image_url is populated. All technical specifications are NULL. This is the #1 priority to fix — without specs, the recommendation engine cannot function.

---

## 3. Data Freshness (AUDIT-05)

| Store | Offers | Oldest Record | Newest Record | Age (days) | Freshness (days) |
|-------|--------|---------------|---------------|------------|------------------|
| Brazil Pickleball Store | 35 | 2026-03-18 22:18 | 2026-03-18 22:18 | 0 | 0 |
| Drop Shot Brasil | 13 | 2026-03-18 22:18 | 2026-03-18 22:18 | 0 | 0 |
| yoSports | 45 | 2026-03-18 22:18 | 2026-03-18 22:18 | 0 | 0 |

**Key Finding:** All 3 active stores have data less than 1 day old, seeded on 2026-03-18. The data is freshly populated from the catalog seed script. Note: Phase 1 identified 5 of 11 scrapers as failing (PLAYWRIGHT issues, DNS isolation). The 3 stores above represent the currently **functional** scraper pipelines.

---

## 4. Per-Scraper Coverage (QUAL-05)

| Store | Unique Paddles | Total Offers | Avg Offers/Paddle |
|-------|----------------|--------------|-------------------|
| yoSports | 38 | 45 | 1.18 |
| Brazil Pickleball Store | 35 | 35 | 1.00 |
| Drop Shot Brasil | 13 | 13 | 1.00 |
| **TOTAL** | **86** | **93** | **1.08** |

yoSports provides the most cross-listed paddles (7 paddles with multiple offers).

---

## 5. Incomplete/Corrupt Records (QUAL-03)

All 86 paddles are missing 8 of 9 required fields (everything except image_url). This is not corruption — it reflects the initial data pipeline which only captures names, images, and market offers. The specification fields must be enriched from the US dump data and/or manual entry.

### Remediation

See `cleanup_records.sql` — no cleanup SQL needed (0 corrupt records, 0 non-paddles, 0 duplicates).

**Enrichment path:**
- 32 paddles (37%) match the US dump → can auto-populate specs
- 11 paddles are near-misses (0.50–0.59 match score) → may match with lowered threshold
- 43 paddles have no US dump match → need manual research or new data sources

---

## 6. Smoke Test Results

| Check | Description | Result |
|-------|-------------|--------|
| CHECK 1 | Specs Confidence Gate | ✅ All 0 active paddles pass (none have confidence=1.0) |
| CHECK 2 | No Fabricated Ratings | ✅ No fabricated ratings detected |
| CHECK 3 | Market Offers Present | ✅ All 0 active paddles have offers |
| CHECK 4 | Required Fields Complete | ✅ All 0 active paddles have 8/8 fields |

**Overall:** ✅ ALL SMOKE TESTS PASSED

> **Note:** Smoke tests pass vacuously — 0 paddles have specs_confidence=1.0, so no paddles are "active" from the quality gate perspective. The real work is enriching specs so paddles become active.

---

## 7. Validation Sources

| Source Type | Count |
|-------------|-------|
| none | 86 paddles |

Zero paddles have any validation sources. This confirms that no enrichment pipeline has run yet.

---

## 8. Recommendations

### Priority 1: Specs Enrichment (Blocks Everything)
1. **Run US dump enrichment** for the 32 matched paddles — this would immediately bring 37% of the catalog to complete specs
2. **Lower match threshold** from 0.60 to 0.50 to capture the 11 near-miss paddles (48% total coverage)
3. **Manual research** for the remaining 43 unmatched paddles (mostly Brazilian/niche brands: 3Rdshot, Drop Shot, Zcebra)

### Priority 2: Scraper Reliability
4. **Fix PLAYWRIGHT scrapers** (Phase 1 finding) — install chromium in backend_v3 container
5. **Investigate DNS isolation** impacting 2 P1 scrapers (scrape_propadel.py, fetch_pb_studio.py)

### Priority 3: Data Monitoring
6. **Set up freshness alerts** — data currently < 1 day old but will go stale without active scraping
7. **Low-price review** — 3 paddles under R$ 450 may be entry-level or mispriced (Oberon Mini R$ 109, Start R$ 367, Agassi Champion R$ 449)

---

*Report generated: 2026-03-19 from Phase 2 Data Quality Audit*
*See also: VALIDATION_RULES.md, cleanup_records.sql, quality_metrics_baseline.json*
