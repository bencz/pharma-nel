# Frontend Architecture Document

## Overview

The Pharma Knowledge frontend is a modern, production-ready React application built with Next.js 14+ using the App Router architecture. It provides an intelligent interface for pharmaceutical entity extraction and analysis using AI-powered Named Entity Recognition (NER) and Named Entity Linking (NEL).

---

## Technology Stack

| Category | Technology | Version |
|----------|------------|---------|
| Framework | Next.js (App Router) | 14+ |
| Language | TypeScript | 5+ (strict mode) |
| Styling | TailwindCSS | 4 |
| UI Components | shadcn/ui | Latest |
| Server State | TanStack Query | 5 |
| Client State | Zustand | 4 |
| Animations | Framer Motion | 11 |
| Icons | Lucide React | Latest |

---

## Architecture Patterns

### 1. Feature-Based Architecture

The codebase follows a feature-based organization pattern, separating concerns by domain rather than technical layer:

```
src/
├── app/                    # Next.js App Router (routes)
├── features/               # Feature modules (self-contained)
│   ├── upload/             # Upload feature
│   └── search/             # Search feature
├── components/             # Shared components
│   ├── ui/                 # Base UI components (shadcn/ui)
│   ├── layout/             # Layout components
│   └── [domain]/           # Domain-specific components
├── hooks/                  # Custom React hooks
├── lib/                    # Utilities and API client
├── store/                  # Zustand stores
├── types/                  # TypeScript type definitions
└── providers/              # React context providers
```

### 2. State Management Strategy

The application uses a **dual-state management** approach:

#### Server State (TanStack Query)
- All data fetching and caching
- Automatic background refetching
- Optimistic updates
- Query key factory pattern for cache management

```typescript
// Example: Query key factory pattern
export const extractionKeys = {
  all: ["extractions"] as const,
  list: (limit: number) => [...extractionKeys.all, "list", limit] as const,
  detail: (id: string) => [...extractionKeys.all, "detail", id] as const,
};
```

#### Client State (Zustand)
- UI state (panels, selections)
- Ephemeral application state
- Clear separation between State and Actions interfaces

```typescript
interface ExtractionState {
  selectedSubstanceId: string | null;
  isDetailsPanelOpen: boolean;
}

interface ExtractionActions {
  setSelectedSubstanceId: (id: string | null) => void;
  openDetailsPanel: () => void;
}

type ExtractionStore = ExtractionState & ExtractionActions;
```

### 3. API Layer Architecture

The API layer follows a **service pattern** with clear separation:

```
lib/api/
├── config.ts       # Base URL, error handling
├── extraction.ts   # Extraction endpoints
├── entity.ts       # Entity/substance endpoints
├── profile.ts      # Profile endpoints
└── index.ts        # Public API exports
```

Each service module exports an object with async methods that handle:
- Request construction
- Response parsing with type safety
- Error transformation via `handleResponse<T>`

### 4. Type System

The type system is organized in layers:

```
types/
├── models/         # Domain models
│   ├── base.ts     # BaseResponse, ApiError
│   ├── entity.ts   # Entity types
│   ├── substance.ts # Substance types
│   ├── profile.ts  # Profile types
│   └── extraction.ts # Extraction types
├── api/
│   └── responses.ts # API response wrappers
└── index.ts        # Public exports
```

All API responses follow a consistent pattern:
```typescript
interface BaseResponse<T> {
  success: boolean;
  data: T | null;
  error: ApiError | null;
}
```

---

## Component Patterns

### 1. Component Structure

Components follow a consistent internal structure:

```typescript
// 1. Imports (external first, then internal)
import { useState } from "react";
import { Button } from "@/components/ui/button";

// 2. Types/Interfaces
interface ComponentProps {
  data: DataType;
  onAction: () => void;
}

// 3. Constants (if any)
const DEBOUNCE_MS = 300;

// 4. Component
export function Component({ data, onAction }: ComponentProps) {
  // 4a. State
  // 4b. Derived state / Queries
  // 4c. Callbacks
  // 4d. Effects (avoid if possible)
  // 4e. Early returns
  // 4f. Main render
}
```

### 2. Hooks Pattern

Custom hooks encapsulate:
- Data fetching logic (TanStack Query wrappers)
- Reusable stateful logic
- Side effect management

All hooks that use React features include the `"use client"` directive.

### 3. Error Handling

Errors are handled at specific boundaries:
- **TanStack Query** - Data fetching errors
- **Error Boundaries** - Component tree protection
- **Toast notifications** - User feedback

Components do NOT use try/catch for rendering logic.

---

## Styling Approach

### TailwindCSS + shadcn/ui

- **Utility-first CSS** with TailwindCSS
- **Component variants** using `class-variance-authority` (CVA)
- **Consistent theming** via CSS custom properties
- **Dark mode support** via `next-themes`

### Design Tokens

```css
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  /* ... */
}
```

---

## Performance Considerations

1. **Code Splitting** - Automatic via Next.js App Router
2. **Query Caching** - TanStack Query with configurable stale times
3. **Prefetching** - Substance data prefetched on extraction success
4. **Optimized Images** - Next.js Image component (where applicable)
5. **Minimal Re-renders** - Zustand selectors for granular subscriptions

---

## Responsive Design

The application is fully responsive with:
- **Mobile-first approach** using Tailwind breakpoints
- **Adaptive layouts** - Sidebar becomes Sheet on mobile
- **Touch-friendly interactions**
- **Sticky headers** for navigation context

Breakpoints:
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

---

## Security Considerations

1. **Environment Variables** - Sensitive config via `NEXT_PUBLIC_*` prefix
2. **Input Validation** - File type and size validation on upload
3. **XSS Prevention** - React's built-in escaping
4. **CORS** - Handled by backend API

---

## Testing Strategy

Recommended testing approach (to be implemented):
- **Unit Tests** - Vitest for hooks and utilities
- **Component Tests** - Testing Library for components
- **E2E Tests** - Playwright for critical user flows

---

## Deployment

### Docker Support

Production and development Dockerfiles provided:
- `docker/Dockerfile` - Multi-stage production build
- `docker/Dockerfile.dev` - Development with hot reload

### Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_PHARMA_API_URL` | Backend API URL |
