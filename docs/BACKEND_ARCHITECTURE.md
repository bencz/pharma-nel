# Pharmaceutical NER/NEL System - Architecture Document

## 1. Overall System Design

### 1.1 Architecture Overview

The system follows a **pragmatic hybrid architecture** optimized for ArangoDB as the primary data store. It combines Domain-Driven Design (DDD) principles with practical simplifications that leverage ArangoDB's native JSON document storage.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER (FastAPI)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   /extract  │  │   /entity   │  │   /health   │  │  Exception Handler  │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘  │   (ONLY try/catch)  │ │
│         │                │                          └─────────────────────┘ │
└─────────┼────────────────┼──────────────────────────────────────────────────┘
          │                │
┌─────────▼────────────────▼──────────────────────────────────────────────────┐
│                            DOMAIN LAYER (Services)                          │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────────┐ │
│  │     NERService      │  │  SubstanceService   │  │ SubstanceEnrichment  │ │
│  │  - extract_from_text│  │  - get_profile      │  │    Service           │ │
│  │  - extract_and_enrich│ │  - enrich_substance │  │  - get_substance_data│ │
│  └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬───────────┘ │
└─────────────┼────────────────────────┼─────────────────────────┼────────────┘
              │                        │                         │
┌─────────────▼────────────────────────▼─────────────────────────▼────────────┐
│                         INFRASTRUCTURE LAYER                                │
│  ┌─────────────────────────────────┐  ┌───────────────────────────────────┐ │
│  │         REPOSITORIES            │  │           HTTP CLIENTS            │ │
│  │  - ExtractionRepository         │  │  - OpenAIClient (NER via LLM)     │ │
│  │  - SubstanceRepository          │  │  - FDAClient (OpenFDA API)        │ │
│  │  - DrugRepository               │  │  - RxNormClient (NIH RxNorm)      │ │
│  │  - OpenFDAGraphRepository       │  │  - UNIIClient (Chemical data)     │ │
│  └─────────────┬───────────────────┘  └─────────────┬─────────────────────┘ │
└────────────────┼────────────────────────────────────┼───────────────────────┘
                 │                                    │
        ┌────────▼────────┐              ┌────────────▼────────────┐
        │    ArangoDB     │              │    External APIs        │
        │  (Graph + Doc)  │              │  FDA, RxNorm, UNII, LLM │
        └─────────────────┘              └─────────────────────────┘
```

### 1.2 Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **ArangoDB (Graph + Document)** | Native graph traversal for drug relationships; JSON documents eliminate ORM overhead |
| **Try-Catch Free Architecture** | Exceptions propagate to global middleware; cleaner business logic |
| **Container Pattern for DI** | Lazy-loaded singletons; easy mocking for tests |
| **Protocol Classes (Ports)** | Interface contracts for external clients; enables swapping implementations |
| **Domain Entities = Persistence** | Since ArangoDB stores JSON, entities serialize directly without mapping layers |

### 1.3 Layer Responsibilities

| Layer | Responsibility | Key Components |
|-------|----------------|----------------|
| **API** | HTTP handling, validation, response formatting | Routes, Schemas (Pydantic), Middleware |
| **Domain** | Business logic, orchestration | Services, Entities, Exceptions |
| **Infrastructure** | External integrations, persistence | Repositories, HTTP Clients, PDF Extractor |
| **Shared** | Cross-cutting concerns | Config, Logging, Utilities |

### 1.4 API Documentation (Swagger/ReDoc)

FastAPI provides automatic API documentation generation via OpenAPI 3.0:

| Endpoint | Interface | Purpose |
|----------|-----------|---------|
| `/docs` | **Swagger UI** | Interactive API explorer with "Try it out" functionality |
| `/redoc` | **ReDoc** | Clean, readable documentation for API consumers |
| `/openapi.json` | **OpenAPI Spec** | Machine-readable spec for client code generation |

**How It Works:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Auto-Generated Documentation                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Pydantic Schemas ──────┐                                              │
│   (request/response)     │                                              │
│                          ├──► FastAPI ──► OpenAPI 3.0 ──► Swagger/ReDoc │
│   Route Decorators ──────┤       │                                      │
│   (@router.get, etc)     │       │                                      │
│                          │       ▼                                      │
│   Docstrings ────────────┘   Validation                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- **Always in Sync**: Documentation is generated from code, never outdated
- **Type Safety**: Pydantic schemas enforce request/response validation
- **Interactive Testing**: Swagger UI allows testing endpoints directly in browser
- **Client Generation**: OpenAPI spec enables automatic SDK generation (TypeScript, Python, etc.)

---

## 2. NER/NEL Approach and Rationale

### 2.1 Named Entity Recognition (NER)

The system uses **LLM-based NER** (OpenAI GPT-4o-mini) for pharmaceutical entity extraction. This approach was chosen over traditional NER models (spaCy, BioBERT) for several reasons:

**Why LLM-based NER:**
- **Domain Flexibility**: Pharmaceutical nomenclature is complex (brand names, generics, development codes, INN names)
- **Context Understanding**: LLMs understand context better than pattern-matching approaches
- **Zero-Shot Capability**: No training data required; works immediately on new drug names
- **Structured Output**: Returns JSON with confidence scores, entity types, and relationships

**Anti-Hallucination Measures:**
The prompt includes strict rules to prevent the LLM from inventing drug names:
1. Extract ONLY entities that appear verbatim in the document
2. Never add "related" or "commonly used" drugs
3. When in doubt, EXCLUDE rather than INCLUDE
4. Validation checklist in prompt output

**Entity Types Extracted:**
- `BRAND`: Trade/brand names (e.g., "KADCYLA", "Advil")
- `GENERIC`: Generic/INN names (e.g., "ibuprofen", "trastuzumab emtansine")
- `CODE`: Development codes (e.g., "AG-120", "BMS-986165")
- `INGREDIENT`: Active pharmaceutical ingredients

### 2.2 Named Entity Linking (NEL)

NEL connects extracted entities to canonical pharmaceutical identifiers:

```
Document Text: "Patient received KADCYLA (trastuzumab emtansine) 3.6mg/kg"
                      │                    │
                      ▼                    ▼
              ┌───────────────┐    ┌───────────────┐
              │ Entity: KADCYLA│   │ Entity: trastu│
              │ Type: BRAND   │    │ Type: GENERIC │
              │ Status: NEL   │    │ Status: NEL   │
              │ linked_to:    │◄──►│ linked_to:    │
              │ trastuzumab   │    │ KADCYLA       │
              │ emtansine     │    │               │
              └───────────────┘    └───────────────┘
```

**NEL Relationship Types:**
- `brand_of`: Brand name OF the linked generic
- `generic_of`: Generic name OF the linked brand
- `same_as`: Same entity, different spelling/format
- `ingredient_of`: Ingredient OF the linked product
- `contains`: Product CONTAINS the linked ingredient

**NEL Confidence Thresholds:**
- 90-100: Certain (link established)
- 70-89: High confidence
- 50-69: Medium confidence
- Below 50: Do not link (status = NER_ONLY)

### 2.3 Extraction Pipeline Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  PDF Upload  │────►│ Text Extract │────►│  LLM (NER)   │────►│ Parse JSON   │
│              │     │  (PyMuPDF)   │     │  GPT-4o-mini │     │  Response    │
└──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                      │
┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│   Return     │◄────│ Persist to   │◄────│   Enrich     │◄───────────┘
│  References  │     │   ArangoDB   │     │  (FDA/RxNorm)│
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## 3. Data Source Integration Strategy

### 3.1 External Data Sources

The system integrates with four external APIs to build a comprehensive pharmaceutical knowledge graph:

| Source | Purpose | Data Retrieved |
|--------|---------|----------------|
| **OpenFDA** | FDA drug approvals, labels, NDC codes | Drug applications, package inserts, adverse events, recalls |
| **RxNorm (NIH)** | Standardized drug nomenclature | RxCUI identifiers, ingredients, brands, drug interactions |
| **UNII/GSRS** | Chemical substance data | SMILES, molecular formula, CAS numbers, InChI keys |
| **OpenAI** | NER/NEL extraction | Entity recognition from unstructured text |

### 3.2 Integration Architecture

```
                    ┌─────────────────────────────────────┐
                    │   SubstanceEnrichmentService        │
                    │   (Orchestrator)                    │
                    └───────────────┬─────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           │                        │                        │
    ┌──────▼──────┐          ┌──────▼──────┐          ┌──────▼──────┐
    │  FDAClient  │          │ RxNormClient│          │  UNIIClient │
    │             │          │             │          │             │
    │ - drugsfda  │          │ - rxcui     │          │ - substance │
    │ - label     │          │ - related   │          │ - structure │
    │ - ndc       │          │ - interact  │          │ - codes     │
    │ - event     │          │ - ndc       │          │             │
    │ - enforce   │          │             │          │             │
    └─────────────┘          └─────────────┘          └─────────────┘
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    ▼
                    ┌─────────────────────────────────────┐
                    │       SubstanceGraphData            │
                    │  (Aggregated enrichment result)     │
                    │                                     │
                    │  - drugs, substances, manufacturers │
                    │  - routes, dosage_forms, pharm_class│
                    │  - reactions, interactions, labels  │
                    │  - applications, products, edges    │
                    └─────────────────────────────────────┘
```

### 3.3 HTTP Client Design

All external clients inherit from `BaseHTTPClient` which provides:
- **Connection Pooling**: httpx.AsyncClient with 100 max connections
- **Retry Logic**: Configurable retries with exponential backoff
- **Rate Limit Handling**: Automatic retry on 429 responses
- **Timeout Management**: Per-client configurable timeouts
- **Structured Logging**: Request/response logging with trace IDs

### 3.4 Data Aggregation Strategy

The `SubstanceEnrichmentService.get_substance_data()` method:

1. **Parallel API Calls**: Uses `asyncio.gather()` to fetch from FDA, RxNorm, UNII concurrently
2. **RxCUI Hint Optimization**: Extracts RxCUI from FDA data to speed up RxNorm lookup
3. **Deduplication**: Entities are keyed by normalized identifiers to prevent duplicates
4. **Edge Creation**: Relationships between entities are captured as graph edges

---

## 4. Performance and Scalability Considerations

### 4.1 Async-First Architecture

**All I/O operations are async:**
- Database queries via `arangoasync`
- HTTP requests via `httpx.AsyncClient`
- File operations where applicable

This enables high concurrency without thread overhead.

### 4.2 Caching Strategy

#### Why Not Redis?

A common question is: "Why not use Redis for caching?" The answer lies in ArangoDB's multi-model capabilities:

**ArangoDB as a Multi-Model Database:**

ArangoDB is not just a graph database—it's a **multi-model database** that supports:
- **Document Store**: JSON documents with flexible schemas
- **Graph Database**: Native graph traversal with AQL
- **Key-Value Store**: O(1) lookups via `_key` field (primary key)

This eliminates the need for a separate caching layer like Redis in most scenarios.

**Key-Value Performance in ArangoDB:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ArangoDB Key-Value Performance                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Operation              │  Complexity  │  Example                       │
├─────────────────────────┼──────────────┼────────────────────────────────┤
│  Lookup by _key         │  O(1)        │  db.extractions.get("abc123")  │
│  Lookup by indexed field│  O(log n)    │  WHERE file_hash == "..."      │
│  Graph traversal        │  O(V + E)    │  FOR v IN 1..2 OUTBOUND ...    │
└─────────────────────────────────────────────────────────────────────────┘
```

**Why This Works for Our Use Case:**

| Scenario | Redis Approach | ArangoDB Approach |
|----------|----------------|-------------------|
| **Extraction cache** | Store JSON in Redis, sync to DB | Direct O(1) lookup by `_key` (file_hash) |
| **Substance lookup** | Cache enriched substances | Index on `name`, `unii` - O(log n) |
| **Session/hot data** | TTL-based cache | Same data already in DB |
| **Graph queries** | Not possible | Native AQL traversal |

**Benefits of Single-Database Approach:**

1. **Consistency**: No cache invalidation complexity—data is always fresh
2. **Simplicity**: One database to manage, backup, and scale
3. **Atomicity**: Transactions span cache and persistent data
4. **Cost**: No additional infrastructure (Redis cluster)
5. **Latency**: ArangoDB with proper indices matches Redis for our workload

**When Redis Would Be Needed:**

Redis would be justified if:
- Sub-millisecond latency is critical (ArangoDB: ~0.1-0.5ms for key lookups, Redis: ~0.05-0.1ms)
- Massive read throughput (>100k ops/sec) on hot keys
- Distributed rate limiting across multiple instances
- Pub/Sub messaging patterns

For this pharmaceutical NER/NEL system, ArangoDB's multi-model capabilities provide sufficient performance while maintaining architectural simplicity.

#### Current Caching Implementation

**Extraction Caching:**
- Extractions are cached by file hash (SHA256)
- Subsequent requests for the same document return cached results
- Cache lookup: O(1) via ArangoDB primary key (`_key` = file_hash)

**Substance Caching:**
- Enriched substances are marked with `is_enriched=True`
- Before enrichment, system checks if substance already exists
- Prevents redundant API calls for known substances
- Lookup by name: O(log n) via persistent index

### 4.3 Database Optimization

**ArangoDB Graph Schema - Entity Relationship Diagram:**

```
                                    ┌─────────────────┐
                                    │   PROFILES      │
                                    │  (user resumes) │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │ profile_has_extraction │ profile_interested_in  │
                    ▼                        │        substance       │
           ┌─────────────────┐               │                        │
           │  EXTRACTIONS    │               │                        │
           │ (NER results)   │               │                        │
           └─────────────────┘               │                        │
                                             ▼                        │
┌──────────────┐    application_for    ┌─────────────────┐            │
│ APPLICATIONS │◄──────────────────────│     DRUGS       │            │
│  (NDA/ANDA)  │                       │                 │            │
└──────────────┘                       └────────┬────────┘            │
                                                │                     │
┌──────────────┐    product_of         ┌────────┴──────┐              │
│   PRODUCTS   │◄──────────────────────┤               │              │
│  (NDC pkgs)  │                       │               │              │
└──────────────┘                       │               │              │
                                       │               │              │
        ┌──────────────────────────────┼───────────────┼──────────────┤
        │              │               │               │              │
        ▼              ▼               ▼               ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐ ┌────────────┐ ┌─────────────┐
│ MANUFACTURERS│ │  ROUTES  │ │ DOSAGE_FORMS │ │PHARM_CLASSES│ │ SUBSTANCES │◄┘
│              │ │          │ │              │ │ (EPC/MOA)  │ │ (chemicals) │
└──────────────┘ └──────────┘ └──────────────┘ └────────────┘ └─────────────┘
        ▲              ▲               ▲               ▲
        │              │               │               │
        └──────────────┴───────────────┴───────────────┘
                    drug_by_manufacturer
                    drug_has_route
                    drug_has_form
                    drug_in_class
                    drug_has_substance

                    ┌─────────────────┐
                    │                 │
        ┌───────────┴─────────────────┴───────────┐
        │                                         │
        ▼                                         ▼
┌──────────────┐                         ┌──────────────┐
│  REACTIONS   │  drug_causes_reaction   │ DRUG_LABELS  │  drug_has_label
│  (adverse)   │◄────────────────────────│ (pkg insert) │◄─────────────────
└──────────────┘                         └──────────────┘

┌──────────────┐
│ INTERACTIONS │  drug_interacts_with
│ (DDI from    │◄─────────────────────────────────────────────────────────
│   RxNorm)    │
└──────────────┘
```

### 4.4 Concurrent Processing

**Parallel Enrichment:**
```python
tasks = [substance_service.enrich_substance(name) for name in names_to_enrich]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Parallel API Fetching:**
```python
results = await asyncio.gather(
    self.search_drugsfda(drug_name),
    self.search_ndc(drug_name),
    self.search_enforcement(drug_name),
)
```

### 4.5 Error Resilience

**Graceful Degradation:**
- Individual API failures don't break the entire enrichment
- `return_exceptions=True` in `asyncio.gather()` captures failures
- Partial results are still persisted and returned

**Exception Hierarchy:**
```
Exception
├── DomainException (400-level, business errors)
│   ├── SubstanceNotFoundError (404)
│   ├── ExtractionFailedError (400)
│   └── InvalidPDFError (400)
├── DatabaseException (500, logged, generic message to client)
└── ClientException (502, external service errors)
```

**Route-Level Error Messages (`@error_message` decorator):**

The system uses a custom `@error_message` decorator to provide user-friendly error messages for unexpected exceptions, preventing internal error details from being exposed:

```python
# src/api/decorators.py
@router.post("/extract")
@error_message("An error occurred while processing your document. Please try again.")
async def extract_entities(...):
    ...
```

**How it works:**
1. Each route can define a custom error message via the `@error_message` decorator
2. When an unhandled exception occurs, the global exception handler retrieves this message
3. The message is returned to the user instead of internal error details
4. If no custom message is defined, a default message is used

**Implementation:**
```python
# In exception_handler.py
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", ...)  # Full details logged
    safe_message = get_safe_error_message(request)  # Get route's custom message
    return JSONResponse(
        status_code=500,
        content=BaseResponse.fail(
            ErrorDetail(code="INTERNAL_ERROR", message=safe_message)
        ).model_dump(),
    )
```

This pattern ensures:
- **Security**: Internal errors are never exposed to users
- **UX**: Users receive contextual, helpful error messages
- **Debugging**: Full error details are logged for developers

### 4.6 Scalability Path

| Concern | Current | Future Scale |
|---------|---------|--------------|
| **Compute** | Single instance | Horizontal scaling via container orchestration |
| **Database** | Single ArangoDB | ArangoDB cluster with sharding |
| **Caching** | In-database | Add Redis for hot data |
| **Rate Limits** | Per-client retry | Distributed rate limiting |
| **LLM Costs** | On-demand | Batch processing, model caching |

### 4.7 Observability

**Structured Logging:**
- JSON format in production
- Trace ID propagation across requests
- Request context (method, path, client_ip) in all logs

**Health Checks:**
- `/health`: Full dependency check (ArangoDB)
- `/health/live`: Simple liveness probe
- `/ready`: Readiness probe for Kubernetes
