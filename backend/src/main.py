"""
FastAPI Application Entrypoint.

Configures the application with:
- Structured logging with trace-id/correlation-id
- Exception handlers (ONLY place for try/catch)
- CORS middleware
- Health check routes
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.exception_handler import register_exception_handlers
from src.api.middleware.logging import RequestLoggingMiddleware
from src.api.routes import entity, extract, health, profile
from src.container import Container
from src.infrastructure.database.initializer import DatabaseInitializer
from src.shared.config import Settings, get_settings
from src.shared.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    settings = get_settings()

    setup_logging(
        log_level=settings.log_level,
        json_logs=settings.log_json and settings.is_production,
    )

    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    container = Container.initialize(settings)

    await DatabaseInitializer(container).initialize()

    yield

    logger.info("application_shutting_down")
    await container.close()
    Container.reset()
    logger.info("application_stopped")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = settings or get_settings()

    setup_logging(
        log_level=settings.log_level,
        json_logs=settings.log_json and settings.is_production,
    )

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Pharmaceutical Named Entity Recognition and Linking API",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    app.add_middleware(RequestLoggingMiddleware)

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(extract.router)
    app.include_router(entity.router)
    app.include_router(profile.router)

    return app


app = create_app()
