# Pharma Knowledge Frontend - Production Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM node:20-alpine AS builder

RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install ALL dependencies (devDependencies needed for build)
RUN npm ci

# Copy source code
COPY . .

# Disable telemetry
ENV NEXT_TELEMETRY_DISABLED=1

# Build-time environment variable for API URL
ARG NEXT_PUBLIC_PHARMA_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_PHARMA_API_URL=${NEXT_PUBLIC_PHARMA_API_URL}

# Build the application
RUN npm run build

# =============================================================================
# Stage 2: Runner (minimal production image)
# =============================================================================
FROM node:20-alpine AS runner

WORKDIR /app

# Production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy only necessary files from builder
# Next.js standalone output includes minimal node_modules
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Runtime configuration
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Start the application
CMD ["node", "server.js"]
