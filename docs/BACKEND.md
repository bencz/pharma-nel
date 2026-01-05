# Pharma NER/NEL API

Pharmaceutical Named Entity Recognition (NER) and Named Entity Linking (NEL) API with knowledge graph persistence.

## Overview

This API extracts pharmaceutical entities from PDF documents (resumes, clinical documents) using LLM-powered NER, links them to external knowledge bases (FDA, RxNorm, UNII), and persists the enriched data to an ArangoDB graph database.

### Key Features

- **NER/NEL Pipeline**: LLM-based entity extraction with FDA/RxNorm/UNII linking
- **Knowledge Graph**: ArangoDB graph with 13 vertex and 13 edge collections
- **Profile Tracking**: Links user profiles to extractions and substances of interest
- **Caching**: File-hash based extraction caching to avoid reprocessing
- **Async Architecture**: Full async/await with httpx clients

### Tech Stack

- **Python 3.11+** with strict type hints
- **FastAPI** for HTTP API
- **ArangoDB** for graph database
- **OpenAI GPT-4** for NER extraction
- **httpx** for async HTTP clients
- **Pydantic** for validation and settings
- **structlog** for structured logging

---

## Quick Start

### Prerequisites

- Python 3.11+
- ArangoDB instance (local or remote)
- OpenAI API Key

### Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS

# Install production dependencies only
pip install -e .

# Install with dev dependencies (for development/testing)
pip install -e ".[dev]"
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required
OPENAI_API_KEY=sk-your-key-here
ARANGO_HOST=http://localhost:8529
ARANGO_DATABASE=pharma_ner
ARANGO_USER=root
ARANGO_PASSWORD=your-password

# Optional
FDA_API_KEY=           # Increases FDA rate limits
OPENAI_MODEL=gpt-4.1-mini
LOG_LEVEL=INFO
```

### Run

```bash
# Development (hot-reload)
uvicorn main:app --reload --port 8000

# Production (single process)
uvicorn main:app --host 0.0.0.0 --port 8000

# Production (multi-process with gunicorn)
gunicorn main:app --bind 0.0.0.0:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Docker

```bash
# Build image
docker build -f docker/Dockerfile -t pharma-ner-api .

# Run container
docker run -d \
  --name pharma-ner \
  -p 8000:8000 \
  --env-file .env \
  pharma-ner-api

# Override workers for different CPU counts
docker run -d \
  -p 8000:8000 \
  -e WORKERS=8 \
  --env-file .env \
  pharma-ner-api
```

**Docker Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKERS` | `4` | Number of gunicorn workers (formula: 2*CPU + 1) |
| `WORKER_TIMEOUT` | `120` | Worker timeout in seconds |
| `KEEPALIVE` | `5` | Keep-alive timeout |
| `MAX_REQUESTS` | `1000` | Restart worker after N requests (memory leak prevention) |

**API**: http://localhost:8000  
**Swagger UI**: http://localhost:8000/docs  
**ReDoc**: http://localhost:8000/redoc  
**OpenAPI JSON**: http://localhost:8000/openapi.json

---

## API Documentation

FastAPI provides automatic interactive API documentation:

| Interface | URL | Description |
|-----------|-----|-------------|
| **Swagger UI** | `/docs` | Interactive API explorer with "Try it out" functionality |
| **ReDoc** | `/redoc` | Clean, readable API documentation |
| **OpenAPI** | `/openapi.json` | OpenAPI 3.0 specification (for code generation) |

Both interfaces are auto-generated from the Pydantic schemas and route definitions, ensuring documentation is always in sync with the code.

---

## API Endpoints

### Health

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Full health check with dependencies |
| `GET /health/live` | Liveness probe (Kubernetes) |
| `GET /ready` | Readiness probe (Kubernetes) |

### Extraction

| Endpoint | Description |
|----------|-------------|
| `POST /extract` | Extract entities from PDF and enrich |
| `GET /extractions` | List recent extractions with profile info |
| `GET /extract/{extraction_id}` | Get extraction by ID |

#### POST /extract

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "extraction_id": "abc123...",
    "profile": {
      "id": "profile-key",
      "full_name": "John Doe",
      "credentials": ["PharmD", "RPh"]
    },
    "entities": [
      {
        "name": "Aspirin",
        "type": "GENERIC",
        "linked_to": "acetylsalicylic acid",
        "relationship": "IS_ACTIVE_INGREDIENT",
        "substance_id": "aspirin",
        "url": "/entity/aspirin"
      }
    ]
  }
}
```

#### GET /extractions

List recent extractions with associated profile information.

```bash
curl http://localhost:8000/extractions?limit=100
```

**Response:**
```json
{
  "success": true,
  "data": {
    "extractions": [
      {
        "key": "d71b36564eab2d49",
        "file_hash": "d71b36564eab2d49",
        "filename": "resume.pdf",
        "status": "completed",
        "created_at": "2026-01-04T12:00:00Z",
        "doc_type": "resume",
        "therapeutic_areas": ["oncology"],
        "drug_density": "MED",
        "total_entities": 5,
        "avg_confidence": 85,
        "profile": {
          "key": "abc123",
          "full_name": "John Doe",
          "credentials": ["PharmD"],
          "email": "john@example.com"
        }
      }
    ],
    "count": 1
  }
}
```

#### GET /extract/{extraction_id}

Get a specific extraction by ID (file_hash).

```bash
curl http://localhost:8000/extract/d71b36564eab2d49
```

Returns the same format as `POST /extract`.

### Profile

| Endpoint | Description |
|----------|-------------|
| `GET /profiles` | List profiles with summary stats |
| `GET /profile/{profile_id}` | Get profile with all related details |

#### GET /profiles

List profiles with extraction and substance counts.

```bash
curl http://localhost:8000/profiles?limit=100
```

**Response:**
```json
{
  "success": true,
  "data": {
    "profiles": [
      {
        "key": "abc123",
        "full_name": "John Doe",
        "credentials": ["PharmD"],
        "email": "john@example.com",
        "extraction_count": 3,
        "substance_count": 5
      }
    ],
    "count": 1
  }
}
```

#### GET /profile/{profile_id}

```bash
curl http://localhost:8000/profile/abc123
```

**Response:**
```json
{
  "success": true,
  "data": {
    "profile": {
      "key": "abc123",
      "full_name": "John Doe",
      "credentials": ["PharmD", "RPh"],
      "email": "john@example.com",
      "phone": "+1234567890",
      "linkedin": "https://linkedin.com/in/johndoe"
    },
    "extractions": [
      {
        "key": "d71b36564eab2d49",
        "filename": "resume.pdf",
        "status": "completed",
        "doc_type": "resume",
        "total_entities": 5
      }
    ],
    "substances": [
      {
        "key": "aspirin",
        "name": "Aspirin",
        "unii": "R16CO5Y76E",
        "is_enriched": true,
        "drugs": [{ "key": "aspirin_325mg", "brand_names": ["Bayer"] }],
        "routes": [{ "key": "oral", "name": "ORAL" }],
        "dosage_forms": [{ "key": "tablet", "name": "TABLET" }],
        "pharm_classes": [{ "key": "nsaid", "name": "NSAID", "class_type": "EPC" }],
        "manufacturers": [{ "key": "bayer", "name": "Bayer Healthcare" }]
      }
    ],
    "stats": {
      "total_extractions": 1,
      "total_substances": 1
    }
  }
}
```

Use `GET /entity/{substance_key}` for full substance details and `GET /extract/{extraction_key}` for full extraction details.

### Entity

| Endpoint | Description |
|----------|-------------|
| `GET /entity/{substance_id}` | Get substance with all graph relations |
| `GET /entity?q=aspirin&limit=20` | Search entities |

```bash
curl http://localhost:8000/entity/aspirin
```

Returns complete substance profile with drugs, manufacturers, routes, dosage forms, pharm classes, labels, applications, products, interactions, and reactions.

---

## Project Structure

```
src/
├── api/                          # HTTP Layer
│   ├── routes/                   # Endpoints
│   │   ├── health.py             # Health checks
│   │   ├── extract.py            # PDF extraction
│   │   └── entity.py             # Entity queries
│   ├── schemas/                  # Pydantic DTOs
│   │   ├── base.py               # BaseResponse[T]
│   │   ├── health.py             # Health schemas
│   │   ├── extract/              # Extraction schemas
│   │   └── entity/               # Entity schemas
│   ├── middleware/               # Exception handlers, logging
│   ├── services/                 # API-level services
│   └── dependencies.py           # FastAPI dependencies
│
├── domain/                       # Business Layer
│   ├── entities/                 # Domain models (@dataclass)
│   │   ├── drug.py               # Drug entity
│   │   ├── substance.py          # Substance entity
│   │   ├── profile.py            # User profile
│   │   ├── extraction.py         # NER extraction result
│   │   └── ...                   # 12 more entities
│   ├── services/                 # Business logic
│   │   ├── ner_service.py        # NER extraction + enrichment
│   │   ├── substance_service.py  # Substance operations
│   │   ├── drug_service.py       # Drug operations
│   │   └── substance_enrichment_service.py
│   ├── exceptions/               # Domain exceptions
│   └── ports/                    # Interfaces (Protocol)
│
├── infrastructure/               # Infrastructure Layer
│   ├── database/
│   │   ├── connection.py         # ArangoDB connection
│   │   ├── initializer.py        # DB/Graph setup
│   │   └── repositories/         # Data access
│   │       ├── base.py           # BaseRepository[T]
│   │       ├── drug_repository.py
│   │       ├── substance_repository.py
│   │       ├── profile_repository.py
│   │       ├── extraction_repository.py
│   │       └── openfda_graph_repository.py
│   ├── clients/                  # External APIs
│   │   ├── base.py               # BaseHTTPClient
│   │   ├── fda_client.py         # FDA OpenFDA
│   │   ├── rxnorm_client.py      # RxNorm
│   │   ├── unii_client.py        # UNII/GSRS
│   │   └── openai_client.py      # OpenAI GPT
│   ├── pdf/                      # PDF extraction
│   └── exceptions/               # Infrastructure exceptions
│
├── shared/                       # Cross-cutting
│   ├── config.py                 # Settings (pydantic-settings)
│   ├── logging.py                # Structured logging
│   └── types.py                  # Type aliases
│
├── prompts/                      # LLM prompts
│   └── ner_extraction.py         # NER system prompt
│
├── container.py                  # Dependency Injection
└── main.py                       # FastAPI app
```

---

## Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────┐
│                  API Layer                  │
│  (routes, schemas, middleware, decorators)  │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│               Domain Layer                  │
│    (entities, services, exceptions)         │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│           Infrastructure Layer              │
│  (database, clients, pdf, exceptions)       │
└─────────────────────────────────────────────┘
```

### Exception Handling

Exceptions propagate to middleware - **no try/catch in business logic**:

```python
# Domain exception
class SubstanceNotFoundError(DomainException):
    status_code = 404
    code = "SUBSTANCE_NOT_FOUND"

# Service - just raise, no catch
async def get_substance(self, id: str) -> Substance:
    substance = await self._repo.find_by_id(id)
    if not substance:
        raise SubstanceNotFoundError(id)
    return substance

# Middleware handles all exceptions globally
```

### Dependency Injection

Container pattern with lazy-loaded singletons:

```python
container = Container.get_instance()

# Sync properties for clients
fda_client = container.fda_client

# Async methods for repositories/services
drug_service = await container.get_drug_service()
```

### Knowledge Graph Schema

**13 Vertex Collections:**
- `drugs`, `substances`, `profiles`, `extractions`
- `manufacturers`, `routes`, `dosage_forms`, `pharm_classes`
- `reactions`, `applications`, `products`, `interactions`, `drug_labels`

**13 Edge Collections:**
- Drug relations: `drug_has_substance`, `drug_has_route`, `drug_has_form`, `drug_in_class`, `drug_by_manufacturer`, `drug_has_label`, `drug_causes_reaction`, `drug_interacts_with`, `drug_alias_of`
- Application/Product: `application_for_drug`, `product_of_drug`
- Profile: `profile_has_extraction`, `profile_interested_in_substance`

---

## Testing

### Unit Tests

```bash
# All unit tests (no external dependencies)
pytest tests/unit -v

# Specific module
pytest tests/unit/domain -v
pytest tests/unit/infrastructure/clients -v
```

### Integration Tests

Requires:
- Running ArangoDB instance
- `OPENAI_API_KEY` environment variable set (tests make real API calls)

```bash
pytest tests/integration -v -m integration
```

### Test Structure

```
tests/
├── conftest.py                 # Global fixtures
├── fixtures/                   # Test data
├── unit/
│   ├── domain/
│   │   ├── entities/           # Entity tests
│   │   └── services/           # Service tests (mocked)
│   ├── infrastructure/
│   │   └── clients/            # Client tests (mocked)
│   └── api/                    # Route tests
└── integration/
    ├── test_entity_routes.py   # Entity endpoint tests
    └── test_extract_routes.py  # Extraction tests
```

---

## Development

### Code Quality

```bash
# Linting
ruff check src tests

# Auto-fix
ruff check src tests --fix

# Format
ruff format src tests

# Type checking
mypy src
```

### Pre-commit

```bash
pre-commit install
pre-commit run --all-files
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `development` | Environment (development/production) |
| `DEBUG` | `false` | Debug mode |
| `LOG_LEVEL` | `INFO` | Log level |
| `LOG_JSON` | `true` | JSON logs in production |
| `ARANGO_HOST` | `http://localhost:8529` | ArangoDB host |
| `ARANGO_DATABASE` | `pharma_ner` | Database name |
| `ARANGO_USER` | `root` | Database user |
| `ARANGO_PASSWORD` | - | Database password |
| `OPENAI_API_KEY` | - | OpenAI API key (required) |
| `OPENAI_MODEL` | `gpt-4.1-mini` | OpenAI model |
| `FDA_API_KEY` | - | FDA API key (optional) |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |

---

## Troubleshooting

### Container not initialized

```bash
# Run via main.py or uvicorn
uvicorn main:app --reload
```

### ArangoDB connection failed

Verify ArangoDB is running and credentials are correct in `.env`.

### OpenAI rate limits

The API uses exponential backoff. For high volume, consider:
- Using `gpt-4.1-mini` (faster, cheaper)
- Implementing request queuing

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `pip install -e ".[dev]"` | Install with dev deps |
| `uvicorn main:app --reload` | Dev server |
| `pytest` | All tests |
| `pytest tests/unit -v` | Unit tests |
| `pytest -m integration` | Integration tests |
| `pytest --cov=src` | Coverage |
| `ruff check src` | Lint |
| `ruff format src` | Format |
| `mypy src` | Type check |

---

## Development Note

> **AI-Assisted Development**: This project utilized AI as an **acceleration tool**, not for "vibe-coding". Specifically, AI was used for:
> - **Code Documentation**: Generating docstrings, comments, and inline documentation
> - **Architecture Documentation**: Creating and maintaining `BACKEND_ARCHITECTURE.md`
> - **Data Class Generation**: Assisting in creating dataclasses from JSON structures defined by the developer
> - **Code Review**: Identifying potential issues and suggesting improvements
>
> All AI-generated content was reviewed, validated, and refined by the developer. The core architecture, business logic, and design decisions were made by human developer!!!
