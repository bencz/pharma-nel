# Pharma Knowledge - NER/NEL Intelligence Platform

A comprehensive pharmaceutical Named Entity Recognition (NER) and Named Entity Linking (NEL) platform that extracts drug entities from PDF documents, enriches them with data from FDA, RxNorm, and UNII databases, and persists the results in an ArangoDB knowledge graph.

## Overview

This platform enables pharmaceutical professionals to:

- **Upload PDF documents** (resumes, clinical documents, research papers)
- **Extract pharmaceutical entities** using LLM-powered NER (GPT-4)
- **Link entities** to canonical identifiers (FDA, RxNorm, UNII)
- **Visualize relationships** in an interactive knowledge graph
- **Search and explore** the pharmaceutical knowledge base

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Next.js 14+)                            │
│                                                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│   │   Upload    │  │  Extraction │  │   Search    │  │    Substance    │    │
│   │   Page      │  │   Results   │  │    Page     │  │     Details     │    │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘    │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │ HTTP/REST
┌────────────────────────────────────▼────────────────────────────────────────┐
│                           BACKEND (FastAPI)                                 │
│                                                                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│   │  /extract   │  │   /entity   │  │  /profiles  │  │    /health      │    │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────────┘    │
│          │                │                │                                │
│   ┌──────▼────────────────▼────────────────▼──────┐                         │
│   │              Domain Services                   │                        │
│   │  NERService, SubstanceService, DrugService    │                         │
│   └──────────────────────┬────────────────────────┘                         │
│                          │                                                  │
│   ┌──────────────────────▼────────────────────────┐                         │
│   │           Infrastructure Layer                 │                        │
│   │  Repositories, HTTP Clients (FDA, RxNorm, UNII)│                        │
│   └──────────────────────┬────────────────────────┘                         │
└──────────────────────────┼──────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────────────┐
│                         ArangoDB (Knowledge Graph)                          │
│                                                                             │
│   Vertices: drugs, substances, profiles, extractions, manufacturers,        │
│             routes, dosage_forms, pharm_classes, reactions, applications,   │
│             products, interactions, drug_labels                             │
│                                                                             │
│   Edges: drug_has_substance, drug_has_route, drug_has_form, drug_in_class,  │
│          drug_by_manufacturer, drug_has_label, drug_causes_reaction,        │
│          drug_interacts_with, profile_has_extraction, ...                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose**
- **OpenAI API Key** (required for NER extraction)

### 1. Clone and Configure

```bash
git clone <repository-url>
cd pharma-nel

# Set required environment variables
export OPENAI_API_KEY=sk-your-key-here
export ARANGO_PASSWORD=pharma123  # Optional, defaults to pharma123
```

### 2. Start Services (Development)

```bash
docker-compose up -d
```

This starts:
- **API**: http://localhost:8000 (Swagger UI: http://localhost:8000/docs)
- **Frontend**: http://localhost:3000
- **ArangoDB**: http://localhost:8529

### 3. Start Services (Production)

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```


---

## Documentation

| Document | Description |
|----------|-------------|
| [Backend](./docs/BACKEND.md) | Backend setup, API endpoints, testing |
| [Backend Architecture](./docs/BACKEND_ARCHITECTURE.md) | NER/NEL approach, data sources, performance |
| [Frontend](./docs/FRONTEND.md) | Frontend setup, features, components |
| [Frontend Architecture](./docs/FRONTEND_ARCHITECTURE.md) | State management, patterns, styling |
| [Knowledge Graph](./docs/KNOWLEDGE_GRAPH.md) | Graph schema, AQL queries, extensions |

---

## API Reference

### Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Full health check with dependencies |
| `/health/live` | GET | Liveness probe (Kubernetes) |
| `/ready` | GET | Readiness probe (Kubernetes) |

### Extraction Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/extract` | POST | Upload PDF and extract entities |
| `/extractions` | GET | List recent extractions |
| `/extract/{id}` | GET | Get extraction by ID |

**Example: Extract entities from PDF**

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "extraction_id": "abc123",
    "profile": {
      "full_name": "John Doe",
      "credentials": ["PharmD"]
    },
    "entities": [
      {
        "name": "Aspirin",
        "type": "GENERIC",
        "linked_to": "acetylsalicylic acid",
        "substance_id": "aspirin"
      }
    ]
  }
}
```

### Profile Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/profiles` | GET | List profiles with stats |
| `/profile/{id}` | GET | Get profile with extractions and substances |

### Entity Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/entity/{id}` | GET | Get substance with all graph relations |
| `/entity` | GET | Search entities (`?q=aspirin&limit=20`) |

**Example: Get substance details**

```bash
curl http://localhost:8000/entity/aspirin
```

Returns complete substance profile with drugs, manufacturers, routes, dosage forms, pharmacological classes, labels, applications, products, interactions, and adverse reactions.

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Environment Variables

### Backend

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `OPENAI_API_KEY` | - | **Yes** | OpenAI API key for NER extraction |
| `ARANGO_HOST` | `http://localhost:8529` | No | ArangoDB host URL |
| `ARANGO_DATABASE` | `pharma_ner` | No | Database name |
| `ARANGO_USER` | `root` | No | Database user |
| `ARANGO_PASSWORD` | - | **Yes** | Database password |
| `OPENAI_MODEL` | `gpt-4.1-mini` | No | OpenAI model for NER |
| `FDA_API_KEY` | - | No | FDA API key (increases rate limits) |
| `ENV` | `development` | No | Environment (development/production) |
| `DEBUG` | `false` | No | Debug mode |
| `LOG_LEVEL` | `INFO` | No | Log level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_JSON` | `true` | No | JSON format logs (production) |
| `CORS_ORIGINS` | `["*"]` | No | Allowed CORS origins |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_PHARMA_API_URL` | `http://localhost:8000` | Backend API URL |

### Docker/Production

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKERS` | `4` | Gunicorn workers (formula: 2*CPU + 1) |
| `WORKER_TIMEOUT` | `120` | Worker timeout in seconds |
| `KEEPALIVE` | `5` | Keep-alive timeout |
| `MAX_REQUESTS` | `1000` | Restart worker after N requests |

---

## Docker Compose Usage

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Production

```bash
# Start with production config
docker-compose -f docker-compose.prod.yml up -d

# Scale workers (adjust WORKERS env var)
WORKERS=8 docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f api

# Stop
docker-compose -f docker-compose.prod.yml down
```

### Environment Variables with Docker

```bash
# Using .env file
echo "OPENAI_API_KEY=sk-xxx" >> .env
echo "ARANGO_PASSWORD=secure-password" >> .env
docker-compose up -d

# Or inline
OPENAI_API_KEY=sk-xxx ARANGO_PASSWORD=secure docker-compose up -d
```

### Services

| Service | Dev Port | Prod Port | Description |
|---------|----------|-----------|-------------|
| `api` | 8000 | 8000 | FastAPI backend |
| `frontend` | 3000 | 3000 | Next.js frontend |
| `arangodb` | 8529 | 8529 | ArangoDB database |

---

## Local Development (Without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp env.example .env.local
# Edit .env.local

# Run development server
npm run dev
```

### ArangoDB

```bash
# Using Docker
docker run -d \
  --name arangodb \
  -p 8529:8529 \
  -e ARANGO_ROOT_PASSWORD=pharma123 \
  arangodb:latest
```

---

## Tech Stack

### Backend

| Technology | Purpose |
|------------|---------|
| Python 3.11+ | Runtime |
| FastAPI | HTTP API framework |
| ArangoDB | Graph database |
| OpenAI GPT-4 | NER extraction |
| httpx | Async HTTP client |
| Pydantic | Validation and settings |
| structlog | Structured logging |

### Frontend

| Technology | Purpose |
|------------|---------|
| Next.js 14+ | React framework (App Router) |
| TypeScript 5+ | Type safety |
| TailwindCSS 4 | Styling |
| shadcn/ui | UI components |
| TanStack Query | Server state |
| Zustand | Client state |
| Framer Motion | Animations |

---

## Testing

### Backend

```bash
cd backend

# Unit tests
pytest tests/unit -v

# Integration tests (requires ArangoDB + OpenAI key)
pytest tests/integration -v -m integration

# Coverage
pytest --cov=src
```

### Frontend

```bash
cd frontend

# Unit tests (when implemented)
npm test
```

---

## Code Quality

### Backend

```bash
cd backend

# Lint
ruff check src tests

# Format
ruff format src tests

# Type check
mypy src
```

### Frontend

```bash
cd frontend

# Lint
npm run lint

# Type check
npm run type-check
```

---

## Troubleshooting

### ArangoDB Connection Failed

1. Verify ArangoDB is running: `docker ps | grep arangodb`
2. Check credentials in environment variables
3. Ensure network connectivity (Docker network or localhost)

### OpenAI Rate Limits

- The API uses exponential backoff for retries
- Consider using `gpt-4.1-mini` for faster/cheaper processing
- Monitor usage in OpenAI dashboard

### Docker Build Issues

```bash
# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Frontend Can't Connect to API

1. Verify `NEXT_PUBLIC_PHARMA_API_URL` is set correctly
2. Check CORS settings in backend (`CORS_ORIGINS`)
3. Ensure API is running and healthy: `curl http://localhost:8000/health`

---

## Sample Results Generator

A Python script is provided to test the API with sample PDF files and generate Markdown reports.

### Usage

```bash
# Ensure the API is running
docker-compose up -d

# Run the script (requires httpx)
pip install httpx
python scripts/generate_sample_results.py

# Custom options
python scripts/generate_sample_results.py \
  --api-url http://localhost:8000 \
  --samples-dir ./samples \
  --output-dir ./results
```

### Output

The script processes all PDF files in `samples/` and generates:
- Individual Markdown reports in `results/` directory
- Profile information extracted from resumes
- Entity tables grouped by type (GENERIC, BRAND, etc.)
- Detailed substance information (UNII, CAS, FDA data)
- Raw API response for debugging

### Sample Files

| File | Description |
|------|-------------|
| `Code_Challenge_Resume_1_-_John_Doe.pdf` | Sample pharmaceutical resume |
| `Code_Challenge_Resume_2_-_Jane_Doe.pdf` | Sample pharmaceutical resume |
| `Code_Challenge_Resume_3_-_Jennifer_Doe.pdf` | Sample pharmaceutical resume |

### Generated Results

After running the script, the following reports will be available:

| Report | Source |
|--------|--------|
| [John Doe Results](./results/Code_Challenge_Resume_1_-_John_Doe_results.md) | Resume 1 |
| [Jane Doe Results](./results/Code_Challenge_Resume_2_-_Jane_Doe_results.md) | Resume 2 |
| [Jennifer Doe Results](./results/Code_Challenge_Resume_3_-_Jennifer_Doe_results.md) | Resume 3 |

---

## Development Notes

> **AI-Assisted Development**: This project utilized AI as an **acceleration tool**, not for "vibe-coding".
>
> **Backend**: AI was used for:
> - **Code Documentation**: Generating docstrings, comments, and inline documentation
> - **Architecture Documentation**: Creating and maintaining architecture documents
> - **Data Class Generation**: Assisting in creating dataclasses from JSON structures
> - **Code Review**: Identifying potential issues and suggesting improvements
>
> **Frontend**: The frontend was developed using AI-assisted programming. The development process was guided and supervised by a human developer who directed the architecture decisions, reviewed code changes, adjusted implementations, and ensured quality standards were met. The AI served as a pair programming assistant, accelerating development while the human maintained creative and technical control over the final product.
>
> All AI-generated content was reviewed, validated, and refined by the developer. The core architecture, business logic, and design decisions were made by human!!
