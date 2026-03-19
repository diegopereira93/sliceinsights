# Scraper Health Status Matrix

**Generated:** 2026-03-19 13:28 UTC  
**Total:** 11 scrapers  
**Results:** 6 PASS / 5 FAIL / 0 TIMEOUT

| Scraper | Category | Status | Root Cause | Transient? | Last Run |
|---------|----------|--------|------------|-----------|----------|
| scrape_joola.py | shopify | PASS | SUCCESS | No | 2026-03-19 |
| scrape_shark.py | shopify | PASS | SUCCESS | No | 2026-03-19 |
| scrape_supremo.py | shopify | PASS | SUCCESS | No | 2026-03-19 |
| scrape_yosports.py | shopify | PASS | SUCCESS | No | 2026-03-19 |
| scrape_pcklhouse.py | shopify | PASS | SUCCESS | No | 2026-03-19 |
| scrape_propadel.py | shopify | PASS | SUCCESS | No | 2026-03-19 |
| scrape_justpaddles.py | playwright | FAIL | PLAYWRIGHT | Yes | 2026-03-19 |
| ingest_pb_studio_csv.py | csv | FAIL | UNKNOWN | No | 2026-03-19 |
| ingest_johnkew_csv.py | csv | FAIL | UNKNOWN | No | 2026-03-19 |
| fetch_johnkew.py | fetcher | FAIL | PLAYWRIGHT | Yes | 2026-03-19 |
| fetch_pb_studio.py | fetcher | FAIL | UNKNOWN | No | 2026-03-19 |

## Failure Details

### scrape_justpaddles.py — PLAYWRIGHT

- **Status:** FAIL
- **Reason:** Playwright browser dependency issue: 'chromium'
- **Transient:** Yes (can retry)
- **Exit code:** 1

```
║                                                            ║
║     playwright install                                     ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
```

### ingest_pb_studio_csv.py — UNKNOWN

- **Status:** FAIL
- **Reason:** Exit code 2, unrecognized error: ingest_pb_studio_csv.py: error: the following arguments are required: --csv
- **Transient:** No (requires fix)
- **Exit code:** 2

```

You may be able to resolve this warning by setting `model_config['protected_namespaces'] = ()`.
  warnings.warn(
usage: ingest_pb_studio_csv.py [-h] --csv CSV [--dry-run]
ingest_pb_studio_csv.py: error: the following arguments are required: --csv
```

### ingest_johnkew_csv.py — UNKNOWN

- **Status:** FAIL
- **Reason:** Exit code 2, unrecognized error: ingest_johnkew_csv.py: error: the following arguments are required: --csv
- **Transient:** No (requires fix)
- **Exit code:** 2

```

You may be able to resolve this warning by setting `model_config['protected_namespaces'] = ()`.
  warnings.warn(
usage: ingest_johnkew_csv.py [-h] --csv CSV [--dry-run]
ingest_johnkew_csv.py: error: the following arguments are required: --csv
```

### fetch_johnkew.py — PLAYWRIGHT

- **Status:** FAIL
- **Reason:** Playwright browser dependency issue: 'chromium'
- **Transient:** Yes (can retry)
- **Exit code:** 1

```
║                                                            ║
║     playwright install                                     ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
```

### fetch_pb_studio.py — UNKNOWN

- **Status:** FAIL
- **Reason:** Exit code 1, no stderr output
- **Transient:** No (requires fix)
- **Exit code:** 1
