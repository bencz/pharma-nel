"""
Integration tests for Entity API routes.

Tests the /entity endpoints with real ArangoDB using testcontainers.
"""

from typing import AsyncGenerator

import httpx
import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.exception_handler import register_exception_handlers
from src.api.middleware.logging import RequestLoggingMiddleware
from src.api.routes import entity, health
from src.container import Container
from src.domain.entities.drug import Drug
from src.domain.entities.substance import Substance

from tests.fixtures.containers import ArangoTestContainer


@pytest.mark.integration
class TestEntityRoutes:
    """Integration tests for /entity endpoints with real ArangoDB."""

    @pytest.fixture(scope="class")
    def arango_container(self) -> ArangoTestContainer:
        """Start ArangoDB container for the test class."""
        container = ArangoTestContainer()
        container.start()
        yield container
        container.stop()

    @pytest.fixture
    async def container(self, arango_container: ArangoTestContainer) -> AsyncGenerator[Container, None]:
        """Create container with real ArangoDB connection."""
        settings = arango_container.get_settings()
        Container.reset()
        container = Container.initialize(settings)
        await container.arango_connection.ensure_database()
        yield container
        await container.close()
        Container.reset()

    @pytest.fixture
    def app_with_db(self, container: Container) -> FastAPI:
        """Create FastAPI app with real database connection."""
        application = FastAPI(title="Test App", version="0.1.0")

        application.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        application.add_middleware(RequestLoggingMiddleware)
        register_exception_handlers(application)

        application.include_router(health.router)
        application.include_router(entity.router)

        return application

    @pytest.fixture
    async def client(self, app_with_db: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Create async test client."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_with_db),
            base_url="http://test",
        ) as client:
            yield client

    @pytest.fixture
    async def seeded_substance(self, container: Container) -> Substance:
        """Seed a test substance in the database."""
        substance_repo = await container.get_substance_repository()
        await substance_repo.ensure_indices()

        substance = Substance(
            key="ibuprofen_test",
            name="IBUPROFEN",
            unii="WK2XYI10QM",
            formula="C13H18O2",
            molecular_weight=206.28,
            smiles="CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
            cas_number="15687-27-1",
            is_enriched=True,
            enriched_at="2024-01-01T00:00:00Z",
        )
        await substance_repo.save(substance)
        return substance

    @pytest.fixture
    async def seeded_drug(self, container: Container) -> Drug:
        """Seed a test drug in the database."""
        drug_repo = await container.get_drug_repository()
        await drug_repo.ensure_indices()

        drug = Drug(
            key="advil_test",
            application_number="NDA018989",
            brand_names=["ADVIL", "Advil Liqui-Gels"],
            generic_names=["ibuprofen"],
            ndc_codes=["00573-0150-01"],
            rxcui=["5640"],
            sponsor_name="Pfizer",
            drug_type="NDA",
            source="test",
            is_enriched=True,
        )
        await drug_repo.save(drug)
        return drug

    async def test_get_substance_details_found(
        self,
        client: httpx.AsyncClient,
        seeded_substance: Substance,
    ) -> None:
        """Test GET /entity/{substance_id} returns substance details."""
        response = await client.get(f"/entity/{seeded_substance.key}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["key"] == seeded_substance.key
        assert data["data"]["name"] == "IBUPROFEN"
        assert data["data"]["unii"] == "WK2XYI10QM"
        assert data["data"]["formula"] == "C13H18O2"

    async def test_get_substance_details_not_found(
        self,
        client: httpx.AsyncClient,
        container: Container,
    ) -> None:
        """Test GET /entity/{substance_id} returns 404 for non-existent substance."""
        response = await client.get("/entity/nonexistent_substance_xyz")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "SUBSTANCE_NOT_FOUND"

    async def test_get_substance_details_by_name(
        self,
        client: httpx.AsyncClient,
        seeded_substance: Substance,
    ) -> None:
        """Test GET /entity/{substance_id} can find by name."""
        response = await client.get("/entity/IBUPROFEN")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "IBUPROFEN"

    async def test_search_entities(
        self,
        client: httpx.AsyncClient,
        seeded_drug: Drug,
    ) -> None:
        """Test GET /entity?q=search returns matching drugs."""
        response = await client.get("/entity", params={"q": "advil", "limit": 10})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

        keys = [r["key"] for r in data["data"]]
        assert seeded_drug.key in keys

    async def test_search_entities_no_results(
        self,
        client: httpx.AsyncClient,
        container: Container,
    ) -> None:
        """Test GET /entity?q=search returns empty list for no matches."""
        response = await client.get(
            "/entity",
            params={"q": "nonexistent_drug_xyz_123", "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    async def test_search_entities_with_limit(
        self,
        client: httpx.AsyncClient,
        container: Container,
    ) -> None:
        """Test GET /entity?q=search respects limit parameter."""
        drug_repo = await container.get_drug_repository()

        for i in range(5):
            drug = Drug(
                key=f"limit_test_{i}",
                brand_names=[f"LimitTestDrug{i}"],
                source="test",
            )
            await drug_repo.save(drug)

        response = await client.get(
            "/entity",
            params={"q": "LimitTestDrug", "limit": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 3


