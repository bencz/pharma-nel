# =============================================================================
# Build Stage
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml .
COPY README.md .
COPY src/ src/

# Install application dependencies
RUN pip install --no-cache-dir .

# Install production server (gunicorn + uvloop for performance)
RUN pip install --no-cache-dir gunicorn uvloop httptools

# =============================================================================
# Production Stage
# =============================================================================
FROM python:3.11-slim AS production

WORKDIR /app

# Install curl for healthcheck (lighter than using Python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ src/
COPY main.py .

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# =============================================================================
# Environment Configuration
# =============================================================================
# Python optimization
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONOPTIMIZE=1

# Gunicorn configuration (can be overridden via docker-compose or k8s)
# Formula for workers: (2 * CPU cores) + 1 for I/O bound applications
ENV WORKERS=4
ENV WORKER_CLASS=uvicorn.workers.UvicornWorker
ENV WORKER_TIMEOUT=120
ENV KEEPALIVE=5
ENV MAX_REQUESTS=1000
ENV MAX_REQUESTS_JITTER=50

# Application defaults (override via .env or docker-compose)
ENV LOG_LEVEL=INFO
ENV LOG_JSON=true

EXPOSE 8000

# =============================================================================
# Health Check
# =============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# =============================================================================
# Entrypoint
# =============================================================================
# Production: gunicorn with uvicorn workers (multi-process, production-grade)
# - UvicornWorker: async workers using uvloop for high performance
# - max-requests: restart workers after N requests to prevent memory leaks
# - access-logfile: stdout for container logging
CMD ["sh", "-c", "gunicorn main:app \
    --bind 0.0.0.0:8000 \
    --workers ${WORKERS} \
    --worker-class ${WORKER_CLASS} \
    --timeout ${WORKER_TIMEOUT} \
    --keep-alive ${KEEPALIVE} \
    --max-requests ${MAX_REQUESTS} \
    --max-requests-jitter ${MAX_REQUESTS_JITTER} \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --enable-stdio-inheritance"]
