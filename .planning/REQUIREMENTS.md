# Requirements: SliceInsights v2.0 Workflows & Automation

**Defined:** 2026-03-19
**Core Value:** Every piece of data flowing into recommendations must be trustworthy.

## v2.0 Requirements

Automation of the entire data pipeline with validated quality gates, real-time monitoring, and reliable deployments.

### CI/CD & Testing

- [x] **CI-01**: GitHub Actions workflow runs on every push to main
- [ ] **CI-02**: Workflow executes unit tests for all scraper modules
- [x] **CI-03**: Workflow executes smoke tests (audit_data_quality.py) for sample scrapers
- [x] **CI-04**: Tests must pass before allowing merge to main
- [x] **CI-05**: Linting/format checks are optional (fail-warn only, not fail-hard)

### SLO Enforcement & Validation

- [x] **SLO-01**: Real-time SLO validation after each scraper completes
- [x] **SLO-02**: Scheduled SLO validation job runs 4x daily (every 6 hours)
- [x] **SLO-03**: Freshness SLO enforced: 24h for Market Offers (prices)
- [x] **SLO-04**: Completeness SLO enforced: 7 days for Product Master Data (specs)
- [x] **SLO-05**: SLO validation results logged and queryable for debugging

### Alerts & Monitoring

- [x] **ALT-01**: Telegram webhook fires when P1 breaches detected (invisible failures, 0 products)
- [x] **ALT-02**: GitHub Issues created automatically for P1 breaches with remediation context
- [x] **ALT-03**: Email alerts sent to admin group on P1 SLO breaches
- [x] **ALT-04**: Alert includes scraper name, breach type, timestamp, last successful run
- [x] **ALT-05**: Alert contains direct link to RUNBOOK_SCRAPERS.md for troubleshooting

### Deploy & Release Strategy

- [ ] **DEP-01**: Nightly batch job aggregates all successful scraper runs
- [ ] **DEP-02**: Pre-deploy validation runs (freshness check, corruption audit)
- [ ] **DEP-03**: Data published to production database after validation passes
- [ ] **DEP-04**: Deploy workflow includes rollback capability if validation fails
- [ ] **DEP-05**: Deploy log recorded with timestamp, scraper count, data records published

### Data Quality Checks & Reporting

- [ ] **QC-01**: Hourly data quality audit job runs for all 11 active scrapers
- [ ] **QC-02**: Audit measures: freshness, completeness, coverage per scraper
- [ ] **QC-03**: Metrics stored in database for historical trending
- [ ] **QC-04**: Quality dashboard endpoint (HTTP GET) returns current metrics as JSON
- [ ] **QC-05**: Weekly quality report generated showing trends and anomalies
- [ ] **QC-06**: Report highlights which scrapers are degrading or improving

## v2.1+ Requirements (Deferred)

### Advanced Automation

- **ADVA-01**: Docker image building and pushing to container registry
- **ADVA-02**: Multi-environment deployments (staging → prod approval gates)
- **ADVA-03**: Automated rollback on data corruption detection
- **ADVA-04**: ML-based anomaly detection for quality metrics
- **ADVA-05**: Automated retry logic with exponential backoff for failed scrapers

## Out of Scope

| Feature | Reason |
|---------|--------|
| Container registry setup | Infrastructure concern; can be v2.1 |
| Real-time data streaming | Batch pipeline sufficient; revisit based on volume growth |
| Multi-region deployments | Single-region sufficient for current scale |
| Kubernetes orchestration | Docker Compose sufficient; revisit if workload increases |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CI-01 | Phase 5 | Complete |
| CI-02 | Phase 5 | Pending |
| CI-03 | Phase 5 | Complete |
| CI-04 | Phase 5 | Complete |
| CI-05 | Phase 5 | Complete |
| SLO-01 | Phase 6 | Complete |
| SLO-02 | Phase 6 | Complete — 06-03 |
| SLO-03 | Phase 6 | Complete — 06-02 |
| SLO-04 | Phase 6 | Complete — 06-02 |
| SLO-05 | Phase 6 | Complete — 06-01 |
| ALT-01 | Phase 7 | Complete |
| ALT-02 | Phase 7 | Complete |
| ALT-03 | Phase 7 | Complete |
| ALT-04 | Phase 7 | Complete |
| ALT-05 | Phase 7 | Complete |
| DEP-01 | Phase 8 | Pending |
| DEP-02 | Phase 8 | Pending |
| DEP-03 | Phase 8 | Pending |
| DEP-04 | Phase 8 | Pending |
| DEP-05 | Phase 8 | Pending |
| QC-01 | Phase 9 | Pending |
| QC-02 | Phase 9 | Pending |
| QC-03 | Phase 9 | Pending |
| QC-04 | Phase 9 | Pending |
| QC-05 | Phase 9 | Pending |
| QC-06 | Phase 9 | Pending |

**Coverage:**
- v2.0 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-19*
*Last updated: 2026-03-19 after defining v2.0 scope*
