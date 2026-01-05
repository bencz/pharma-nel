"""
Global test fixtures.
"""

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from src.api.middleware.exception_handler import register_exception_handlers
from src.api.middleware.logging import RequestLoggingMiddleware
from src.api.routes import health
from src.container import Container
from src.domain.services.drug_service import DrugService
from src.infrastructure.database.repositories.drug_repository import DrugRepository
from src.infrastructure.database.repositories.openfda_graph_repository import OpenFDAGraphRepository
from src.shared.config import API_V1_PREFIX, Settings
from src.shared.logging import setup_logging

pytest_plugins = []


@pytest.fixture
def test_settings() -> Settings:
    """Test settings with safe defaults."""
    return Settings(
        environment="test",
        debug=True,
        log_level="DEBUG",
        log_json=False,
        http_verify_ssl=False,
    )


@pytest.fixture(scope="session")
def integration_settings() -> Settings:
    """Settings for integration tests using running ArangoDB."""
    return Settings(
        environment="test",
        debug=True,
        log_level="DEBUG",
        log_json=False,
        http_verify_ssl=False,
        arango_host="http://localhost:8529",
        arango_database="pharma_ner_test",
        arango_user="root",
        arango_password="pharma123",
    )


@pytest.fixture(scope="function")
async def integration_container(integration_settings: Settings) -> AsyncGenerator:
    """Container configured for integration tests with real ArangoDB."""
    Container.reset()
    container = Container.initialize(integration_settings)
    await container.arango_connection.ensure_database()
    yield container
    await container.close()
    Container.reset()


@pytest.fixture(scope="function")
async def arango_db(integration_container: Container):
    """Get database instance from container."""
    return await integration_container.arango_connection.get_db()


@pytest.fixture(scope="function")
async def drug_repository(integration_container: Container) -> DrugRepository:
    """Get drug repository from container."""
    repo = await integration_container.get_drug_repository()
    await repo.ensure_indices()
    return repo


@pytest.fixture(scope="function")
async def graph_repository(integration_container: Container) -> OpenFDAGraphRepository:
    """Get graph repository from container."""
    repo = await integration_container.get_openfda_graph_repository()
    await repo.ensure_graph()
    return repo


@pytest.fixture(scope="function")
async def drug_service(integration_container: Container) -> DrugService:
    """Get drug service from container."""
    return await integration_container.get_drug_service()


@pytest.fixture
def app(test_settings: Settings):
    """Create test application with test settings."""
    Container.reset()
    Container.initialize(test_settings)

    setup_logging(log_level="DEBUG", json_logs=False)

    application = FastAPI(
        title=test_settings.app_name,
        version=test_settings.app_version,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(application)
    application.include_router(health.router, prefix=API_V1_PREFIX)

    yield application
    Container.reset()


@pytest.fixture
def client(app) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def container(test_settings: Settings) -> Container:
    """Create test container."""
    Container.reset()
    container = Container.initialize(test_settings)
    yield container
    Container.reset()
