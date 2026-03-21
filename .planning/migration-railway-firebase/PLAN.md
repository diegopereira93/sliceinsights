# Migration Plan: Railway PostgreSQL → Firebase Firestore

**Date:** 2026-03-21  
**Status:** Planning  
**Goal:** Replace Railway PostgreSQL with Firebase Firestore to resolve connection reliability issues with Railway's public TCP proxy.

---

## 1. Executive Summary

| Aspect | Current (PostgreSQL) | Target (Firestore) |
|--------|---------------------|---------------------|
| Type | Relational SQL | Document NoSQL |
| Driver | asyncpg + psycopg2 | google-cloud-firestore |
| Connection | TCP (Railway proxy) | HTTPS (Google-managed) |
| Reliability | Degraded (Railway issues) | High (Google SLA) |
| Joins | Native SQL JOINs | Denormalized documents |
| Embeddings | pgvector | Vertex AI (external) |

### Critical Differences

| Challenge | Impact | Mitigation |
|-----------|--------|------------|
| No JOINs | High | Denormalize product+offer data |
| No ARRAY type | Medium | Store as Firestore arrays |
| No pgvector | High | Migrate to Vertex AI or remove semantic search |
| Auto-increment IDs | Medium | Use Firestore auto-IDs or UUIDs |
| Sync+Async drivers | Low | Use async client throughout |

---

## 2. Data Model Mapping (SQL → NoSQL)

### Collection Design

```
firestore_root/
├── brands/              # Brand definitions (static, ~10 docs)
│   └── {brand_id}/
├── paddles/             # PaddleMaster + inline specs (~500 docs)
│   └── {paddle_id}/
├── market_offers/       # Current pricing (high volume, volatile)
│   └── {offer_id}/
├── stores/              # Store definitions (static, ~10 docs)
│   └── {store_id}/
├── slo_logs/            # SLO validation history
│   └── {log_id}/
├── slo_alerts/          # Alert throttle state
│   └── {alert_id}/
├── deploy_logs/         # Deploy batch history
│   └── {log_id}/
├── quality_metrics/     # Quality metric snapshots
│   └── {metric_id}/
├── price_snapshots/      # Historical pricing (time-series)
│   └── {snapshot_id}/
├── price_alerts/         # User price alerts
│   └── {alert_id}/
├── leads/                # Lead capture
│   └── {lead_id}/
└── price_history/        # Denormalized price history per paddle
    └── {paddle_id}/
```

### Model-by-Model Mapping

| SQL Table | Firestore Collection | Document Structure | Complexity |
|-----------|---------------------|-------------------|------------|
| `brands` | `brands/{id}` | `{id, name, website}` | Low |
| `paddle_master` | `paddles/{id}` | `{id, brand_id, brand_name*, ...all fields}` | Medium |
| `market_offers` | `market_offers/{id}` | `{id, paddle_id, store_id, price_brl, url, is_active, last_updated}` | Medium |
| `stores` | `stores/{id}` | `{id, name, base_url, is_active, available_brands[]}` | Low |
| `slo_logs` | `slo_logs/{id}` | `{id, scraper_name, metric_type, value_hours, threshold_hours, status, checked_at, details}` | Low |
| `slo_alerts` | `slo_alerts/{id}` | `{id, scraper_name, metric_type, last_alert_time, status, alert_count, created_at, updated_at}` | Low |
| `deploy_logs` | `deploy_logs/{id}` | `{id, batch_id, version_id, status, ...all fields}` | Low |
| `quality_metrics` | `quality_metrics/{id}` | `{id, scraper_name, run_id, ...all fields}` | Low |
| `price_snapshots` | `price_snapshots/{id}` | `{id, paddle_id, store_name, price_brl, snapshot_date, ...}` | Low |
| `price_alerts` | `price_alerts/{id}` | `{id, paddle_id, user_email, target_price, is_active, created_at}` | Low |
| `leads` | `leads/{id}` | `{id, email, name, converted_from, created_at}` | Low |
| `ai_knowledge` | `ai_knowledge/{id}` | **REMOVE** - migrate to Vertex AI | High |
| `price_history` | `price_history/{paddle_id}` | `{paddle_id, dates: {YYYY-MM-DD: {store: price}}}` (denormalized) | Medium |

### Data Type Translations

| PostgreSQL | Firestore |
|-----------|-----------|
| `INTEGER` (auto) | Auto-ID or `uuid4()` |
| `UUID` | `uuid4()` string |
| `VARCHAR`, `TEXT` | `string` |
| `BOOLEAN` | `boolean` |
| `INTEGER`, `BIGINT` | `integer` |
| `FLOAT`, `DECIMAL` | `double` |
| `TIMESTAMP` | Firestore `timestamp` or ISO string |
| `JSONB` | `map` |
| `ARRAY(String)` | Firestore `array<string>` |
| `ARRAY(Vector)` | **Not supported** → Vertex AI |

---

## 3. Library Selection

### Option A: `google-cloud-firestore` (Recommended)

```bash
# Install
pip install google-cloud-firestore

# Async client (preferred for FastAPI)
from google.cloud.firestore_v1 import AsyncClient

# Sync client (for scripts)
from google.cloud.firestore import Client
```

**Pros:**
- Official Google library
- Async support via `AsyncClient`
- Well-maintained
- Full Firestore feature set

**Cons:**
- More verbose than SQLModel
- No ORM-like abstraction

### Option B: `firebase-admin` (Alternative)

```bash
pip install firebase-admin
```

**Pros:**
- Full Firebase suite access
- Auth, Firestore, Cloud Functions

**Cons:**
- Admin SDK (server-side only)
- Slightly more complex initialization

### Recommendation

Use **`google-cloud-firestore`** with `AsyncClient` for FastAPI routes and sync `Client` for scripts.

---

## 4. File-by-File Changes

### 4.1 `app/config.py`

```python
# REMOVE
database_url: str = Field(...)
database_url_sync: Optional[str] = Field(...)

# ADD
firebase_credentials_path: str = Field(
    default="firebase-credentials.json",
    alias="FIREBASE_CREDENTIALS_PATH"
)
firebase_project_id: str = Field(
    default="",
    alias="FIREBASE_PROJECT_ID"
)
firebase_database_id: str = Field(
    default="(default)",
    alias="FIREBASE_DATABASE_ID"
)
```

**Estimated Effort:** 1 hour  
**Risk:** Low

---

### 4.2 `app/db/database.py` → `app/db/firestore.py` (New)

Replace entire file with Firestore initialization:

```python
from google.cloud.firestore_v1 import AsyncClient
from google.cloud.firestore import Client
from functools import lru_cache
from app.config import get_settings

@lru_cache
def get_async_client() -> AsyncClient:
    settings = get_settings()
    return AsyncClient(
        project=settings.firebase_project_id,
        database=settings.firebase_database_id or "(default)"
    )

@lru_cache
def get_sync_client() -> Client:
    settings = get_settings()
    return Client(
        project=settings.firebase_project_id,
        database=settings.firebase_database_id or "(default)"
    )

# Remove: init_db(), sync_engine, async_engine, Session, etc.
```

**Estimated Effort:** 4-6 hours  
**Risk:** Medium (all queries must be rewritten)

---

### 4.3 `app/models/*.py` → Data Classes

Replace SQLModel tables with Pydantic dataclasses for serialization.

**Example: `app/models/brand.py`**

```python
from pydantic import BaseModel
from typing import Optional

class Brand(BaseModel):
    id: str  # Firestore document ID
    name: str
    website: Optional[str] = None

class BrandCreate(BaseModel):
    name: str
    website: Optional[str] = None

class BrandRead(BaseModel):
    id: str
    name: str
    website: Optional[str] = None
```

**Per-Model Effort:**

| Model | Current Lines | New Lines | Effort |
|-------|--------------|-----------|--------|
| brand.py | 31 | 20 | 1h |
| paddle.py | 261 | 180 | 4h |
| market_offer.py | 47 | 35 | 1h |
| store.py | 30 | 20 | 1h |
| slo.py | 19 | 20 | 1h |
| slo_alert.py | 39 | 35 | 1h |
| deploy_log.py | 21 | 25 | 1h |
| quality_metric.py | 24 | 25 | 1h |
| price_snapshot.py | 24 | 25 | 1h |
| price_alert.py | 19 | 20 | 1h |
| lead.py | 25 | 20 | 1h |
| ai_knowledge.py | **REMOVE** | - | 8h |

**Total Model Effort:** ~22 hours

---

### 4.4 `app/api/routes.py`

**Key Changes:**

| Endpoint | Query Pattern | New Pattern |
|----------|--------------|-------------|
| `/brands` | `select(Brand).join(PaddleMaster)` | Two queries: fetch brands, then paddles |
| `/paddles` | Complex JOIN with subqueries | Denormalized `paddles` with embedded offers |
| `/paddles/{id}` | JOIN for brand + offers | Single doc fetch with subcollections |
| `/search` | Full table scan | Firestore `where('model_name', '>=', q)` |
| `/recommendations` | Multiple JOINs | Denormalized data + client-side filtering |
| `/leads` | Simple CRUD | `add()` → `await client.collection('leads').add(doc)` |
| `/health` | `SELECT 1` | Ping Firestore metadata |

**Estimated Effort:** 8-12 hours  
**Risk:** High (query optimization needed)

---

### 4.5 `app/api/endpoints/history.py`

```python
# BEFORE: SQL JOINs on price_snapshots
# AFTER: Query `price_snapshots` collection filtered by paddle_id and date range
```

**Estimated Effort:** 2 hours  
**Risk:** Medium

---

### 4.6 `app/api/endpoints/alerts.py`

```python
# BEFORE: SQLModel CRUD with Session
# AFTER: Firestore document operations
```

**Estimated Effort:** 2 hours  
**Risk:** Low

---

### 4.7 `app/api/endpoints/quality.py`

```python
# BEFORE: Complex SQL with DISTINCT ON, ORDER BY, subqueries
# AFTER: Query quality_metrics collection, group by scraper_name in Python
```

**Estimated Effort:** 2 hours  
**Risk:** Medium

---

### 4.8 `app/services/recommendation_engine.py`

**Major rewrite needed:**

```python
# BEFORE: SQL JOINs + SQLModel
# AFTER: 
# 1. Fetch paddles (denormalized with brand)
# 2. Fetch offers in batch (paddle_ids)
# 3. Filter/sort in Python
```

**Estimated Effort:** 6-8 hours  
**Risk:** High (performance regression)

---

### 4.9 `app/services/slo_alerts.py`

```python
# BEFORE: SQL queries for throttle dedup
# AFTER: Firestore queries for alert state
```

**Estimated Effort:** 2 hours  
**Risk:** Low

---

### 4.10 `app/db/ingestor.py`

**Major rewrite - this is the core data pipeline:**

```python
# BEFORE: SQLModel Session with commits
# AFTER: Firestore batch writes
from google.cloud.firestore import BatchWriter

async def ingest_rows(rows, store_id, firestore_client):
    batch = firestore_client.batch()
    # Get/create brand doc
    # Get/create paddle doc
    # Upsert market_offer doc
    batch.commit()
```

**Estimated Effort:** 6-8 hours  
**Risk:** High (data consistency)

---

### 4.11 Scripts

| Script | Changes Required | Effort |
|--------|-----------------|--------|
| `scripts/alert_worker.py` | Replace SQLModel Session with Firestore Client | 3h |
| `scripts/slo_validator.py` | Replace SQLModel Session with Firestore Client | 3h |
| `scripts/quality_aggregator.py` | Replace SQL queries with Firestore queries | 3h |
| `scripts/quality_report.py` | Replace SQL queries with Firestore queries | 2h |
| `scripts/deploy_worker.py` | Replace SQL writes with Firestore batch | 4h |
| `scripts/deploy_validator.py` | Replace SQL queries with Firestore queries | 3h |
| `scripts/scrape_*.py` (12 files) | Replace SQLModel with Firestore batch writes | 2h each = 24h |
| `scripts/enrich_paddles.py` | Replace SQLModel with Firestore updates | 2h |
| `scripts/measure_*.py` | Replace SQL queries with Firestore queries | 1h each = 2h |
| `scripts/audit_data_quality.py` | Replace SQL queries with Firestore queries | 2h |

**Total Scripts Effort:** ~50 hours

---

### 4.12 `app/models/ai_knowledge.py` - Vector Embeddings

**PROBLEM:** Firestore does NOT support vector storage.

**Options:**

| Option | Pros | Cons | Effort |
|--------|------|------|--------|
| **A. Vertex AI** | Full semantic search | Extra GCP service, cost | 16h |
| **B. Remove AI Knowledge** | Simple | Lose AI context | 1h |
| **C. Pinecone/Weaviate** | Dedicated vector DB | Extra service | 12h |

**Recommendation:** Option B (Remove) for MVP, migrate to Vertex AI (Option A) in Phase 2.

**Changes:**
1. Remove `ai_knowledge` collection entirely
2. Update LLM prompts to not reference embedded knowledge
3. Archive existing data to JSON backup

---

## 5. Data Migration Strategy

### Phase 1: Export Current Data

```bash
# Export each table to JSON
psql $DATABASE_URL -c "COPY (SELECT row_to_json(t) FROM table_name t) TO STDOUT" > data.json
```

### Phase 2: Transform & Import

```python
import firebase_admin
from firebase_admin import firestore

firebase_admin.initialize_app()
db = firestore.client()

def migrate_table(json_file, collection_name):
    with open(json_file) as f:
        for line in f:
            doc = json.loads(line)
            # Convert snake_case to camelCase (optional)
            # Convert UUID strings
            # Handle ARRAY → Firestore array
            db.collection(collection_name).add(doc)
```

### Phase 3: Verify

```python
# Count verification
pg_count = psql_count("SELECT COUNT(*) FROM table")
fs_count = db.collection('collection').count().get()

if pg_count == fs_count:
    print(f"Migration OK: {collection_name}")
else:
    print(f"MISMATCH: {collection_name} - PG:{pg_count} FS:{fs_count}")
```

### Migration Order

1. **Static data first** (low risk, no dependencies):
   - `brands`
   - `stores`
   - `leads`

2. **Core catalog** (foreign key dependencies):
   - `paddle_master` (with brand embedded)
   - `market_offers` (with paddle_id reference)

3. **Metrics/logs** (high volume):
   - `slo_logs`
   - `slo_alerts`
   - `deploy_logs`
   - `quality_metrics`

4. **Time-series** (highest volume):
   - `price_snapshots` (last 90 days)
   - `price_alerts`

5. **Skip**:
   - `ai_knowledge` (vector data → archive only)

---

## 6. Estimated Effort by Component

| Component | Hours | Risk |
|-----------|-------|------|
| Configuration changes | 2 | Low |
| Firestore client setup | 6 | Medium |
| Model rewrites (12 models) | 22 | Medium |
| API routes rewrites | 16 | High |
| Services rewrites | 16 | High |
| Script rewrites (20+ scripts) | 50 | High |
| AI Knowledge handling | 8 | High |
| Data migration scripts | 12 | High |
| Testing & validation | 20 | High |
| **Total** | **~152 hours** | |

### Phased Approach (Recommended)

| Phase | Scope | Hours | Deliverable |
|-------|-------|-------|-------------|
| **Phase 1** | Core setup + static data | 30h | Firestore client, brands/stores/leads working |
| **Phase 2** | Product catalog | 40h | Paddles + offers + API endpoints |
| **Phase 3** | Metrics & monitoring | 30h | SLO logs, quality metrics, alerts |
| **Phase 4** | Scripts migration | 40h | All scraper/worker scripts updated |
| **Phase 5** | Cleanup & optimization | 12h | Remove ai_knowledge, optimize queries |

---

## 7. Risks and Mitigations

### Risk 1: Query Performance Regression

**Description:** Firestore queries are limited compared to SQL. Complex JOINs become multiple round-trips.

**Mitigation:**
- Denormalize frequently-joined data (paddles with brand embedded)
- Use Firestore `array_contains` for tag/category queries
- Implement caching layer (Redis or in-memory) for expensive queries
- Consider BigTable for high-volume time-series (price_snapshots)

**Fallback:** Keep PostgreSQL for complex analytics, use Firestore for CRUD only.

---

### Risk 2: Cost Explosion

**Description:** Firestore charges per read/write. High-volume scrapers (12 stores × 500 products × daily = 6,000 writes/day = 180K/month).

**Mitigation:**
- Use batch writes (max 500 ops/batch)
- Enable compression on JSON fields
- Set up billing alerts at $50, $100, $200
- Use Spark plan (free tier: 50K reads, 20K writes, 20K deletes/day)

**Actual Estimate:** ~$15-30/month for current workload.

---

### Risk 3: Connection Reliability

**Description:** Still depends on external network to Google Cloud.

**Mitigation:**
- Firestore has Google's global CDN and SLA
- Implement retry logic with exponential backoff
- Use connection pooling via singleton client pattern

---

### Risk 4: Data Consistency

**Description:** No transactions across collections (unlike PostgreSQL).

**Mitigation:**
- Use Firestore transactions for critical operations (e.g., deploy validation)
- Accept eventual consistency for non-critical reads
- Denormalize to reduce cross-collection operations

---

### Risk 5: Vector Search Loss

**Description:** Cannot do semantic search on `ai_knowledge` embeddings.

**Mitigation:**
- Phase 1: Archive existing vectors, disable semantic search
- Phase 2: Add Vertex AI Matching Engine or Pinecone
- Alternative: Use Firestore + Algolia hybrid for full-text + semantic

---

### Risk 6: Vendor Lock-in

**Description:** Moving from Firestore back would be expensive.

**Mitigation:**
- Abstract data access layer (repository pattern)
- Keep data model documented
- Export data regularly to cold storage (GCS)

---

## 8. Testing Strategy

### Unit Tests

```python
# tests/test_firestore_client.py
def test_brand_crud():
    client = get_test_client()
    brand = Brand(name="TestBrand", website="https://test.com")
    doc_id = await create_brand(client, brand)
    fetched = await get_brand(client, doc_id)
    assert fetched.name == "TestBrand"
```

### Integration Tests

```python
# tests/test_api_integration.py
@pytest.mark.asyncio
async def test_list_paddles():
    # Seed test data
    # Call API
    # Verify response
```

### Migration Validation

```python
# scripts/validate_migration.py
def verify_counts():
    pg_tables = ['brands', 'paddles', 'market_offers', ...]
    for table in pg_tables:
        pg_count = count_pg(table)
        fs_count = count_firestore(table)
        assert pg_count == fs_count, f"Mismatch in {table}"
```

---

## 9. Environment Variables

### Before (PostgreSQL)

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
DATABASE_URL_SYNC=postgresql://user:pass@host:5432/db
```

### After (Firestore)

```bash
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=/secrets/firebase-credentials.json
FIREBASE_DATABASE_ID=(default)  # or custom database ID

# Optional: Remove old vars
# DATABASE_URL=
# DATABASE_URL_SYNC=
```

### Firebase Credentials File

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk@....iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

---

## 10. Rollback Plan

If Firestore migration fails or causes critical issues:

1. **Keep Railway PostgreSQL running** (do NOT delete)
2. **Feature flag** the Firestore client in `app/config.py`:
   ```python
   use_firestore: bool = Field(default=False, alias="USE_FIRESTORE")
   ```
3. **Dual-write mode** (optional): Write to both during transition
4. **Quick revert**: Set `USE_FIRESTORE=false`, redeploy

---

## 11. Dependencies to Remove

```bash
# Remove from requirements.txt
sqlmodel==0.0.14
asyncpg==0.29.0
psycopg2-binary==2.9.9
alembic==1.13.1
pgvector==0.2.1

# Add
google-cloud-firestore>=7.0.0
firebase-admin>=7.0.0
```

---

## 12. Summary Checklist

- [ ] Create Firebase project and enable Firestore
- [ ] Generate service account credentials
- [ ] Install `google-cloud-firestore` library
- [ ] Update `app/config.py` with Firebase settings
- [ ] Create `app/db/firestore.py` with client initialization
- [ ] Convert 12 models from SQLModel to Pydantic dataclasses
- [ ] Rewrite `app/api/routes.py` with Firestore queries
- [ ] Rewrite `app/api/endpoints/*.py` with Firestore queries
- [ ] Rewrite `app/services/recommendation_engine.py`
- [ ] Rewrite `app/services/slo_alerts.py`
- [ ] Rewrite `app/db/ingestor.py` with batch writes
- [ ] Update 20+ scripts to use Firestore client
- [ ] Handle `ai_knowledge` (archive vectors)
- [ ] Write data migration scripts
- [ ] Export PostgreSQL data to JSON
- [ ] Import data to Firestore
- [ ] Run validation checks
- [ ] Update environment variables
- [ ] Deploy to staging
- [ ] Run integration tests
- [ ] Deploy to production
- [ ] Monitor costs and performance

---

## 12. Appendix: Firestore Query Reference

### Common Patterns

```python
# Get single document
doc = await db.collection('brands').document('brand-123').get()

# Query with filter
query = db.collection('paddles').where('brand_id', '==', 'brand-123')
results = [doc async for doc in query.stream()]

# Create document
db.collection('brands').add({'name': 'NewBrand', 'website': None})

# Update document
db.collection('brands').document('brand-123').update({'website': 'https://...'})

# Delete document
db.collection('brands').document('brand-123').delete()

# Batch write
batch = db.batch()
batch.set(ref1, data1)
batch.update(ref2, data2)
batch.commit()

# Transaction
@firestore.transactional
def update_in_transaction(transaction, doc_ref):
    snapshot = doc_ref.get(transaction=transaction)
    # ... modify ...
    transaction.update(doc_ref, {'count': new_value})

# Timestamp
from google.cloud.firestore import SERVER_TIMESTAMP

db.collection('logs').add({
    'created': SERVER_TIMESTAMP
})
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-03-21  
**Author:** Claude Code Assistant
