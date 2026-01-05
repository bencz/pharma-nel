# Pharma Knowledge Frontend

Modern, professional frontend for the Pharma Knowledge NER/NEL Intelligence Platform.

> **Development Note**: This frontend was developed using AI-assisted programming (Windsurf/Cascade). The development process was guided and supervised by a human developer who directed the architecture decisions, reviewed code changes, adjusted implementations, and ensured quality standards were met. The AI served as a pair programming assistant, accelerating development while the human maintained creative and technical control over the final product.

## Tech Stack

- **Next.js 14+** - App Router, Server Components
- **TypeScript 5+** - Strict mode enabled
- **TailwindCSS 4** - Utility-first CSS
- **shadcn/ui** - Accessible component library
- **TanStack Query** - Server state management
- **Zustand** - Client state management
- **Framer Motion** - Animations
- **Lucide Icons** - Icon library

## Features

- **PDF Upload** - Drag & drop pharmaceutical documents
- **Entity Extraction** - AI-powered NER/NEL visualization
- **Substance Details** - Complete substance profiles with molecular data
- **SMILES Rendering** - Chemical structure visualization via PubChem
- **Entity Search** - Search the knowledge graph

## Getting Started

### Prerequisites

- Node.js 20+
- Backend API running (see [BACKEND.md](./BACKEND.md))

### Installation

```bash
npm install
```

### Configuration

```bash
cp env.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_PHARMA_API_URL=http://localhost:8000
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Production Build

```bash
npm run build
npm start
```

## Docker

### Production

```bash
cd docker
docker-compose up frontend
```

### Development

```bash
cd docker
docker-compose up frontend-dev
```

### Build Image

```bash
docker build -f docker/Dockerfile -t pharma-frontend --build-arg NEXT_PUBLIC_PHARMA_API_URL=http://api:8000 .
```

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home (Upload)
│   └── search/             # Search page
├── components/
│   ├── layout/             # Header, Footer
│   ├── results/            # Extraction results
│   ├── substance/          # Substance details, molecule viewer
│   ├── ui/                 # shadcn/ui components
│   └── upload/             # File dropzone
├── features/
│   ├── search/             # Search page feature
│   └── upload/             # Upload page feature
├── hooks/                  # Custom React hooks
├── lib/                    # Utilities, API client
├── providers/              # React providers
├── store/                  # Zustand stores
└── types/                  # TypeScript types
```

## API Integration

The frontend connects to the backend API:

| Endpoint | Description |
|----------|-------------|
| `POST /extract` | Upload PDF for entity extraction |
| `GET /entity/{id}` | Get substance details |
| `GET /entity?q=` | Search entities |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_PHARMA_API_URL` | `http://localhost:8000` | Backend API URL |

## Architecture

For detailed architecture documentation, see [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md).

## Code Style

This project follows strict TypeScript and React best practices as defined in the project's coding standards. Key patterns include:

- **Feature-based organization** - Code organized by domain, not technical layer
- **Dual state management** - TanStack Query for server state, Zustand for client state
- **Query key factories** - Consistent cache key management
- **Type-safe API layer** - Full TypeScript coverage with runtime validation
- **Component composition** - Prefer composition over configuration
