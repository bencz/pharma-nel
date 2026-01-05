"""
Integration tests for Extract API routes.

Tests the /extract endpoint with REAL requests:
- Real ArangoDB using testcontainers
- Real PDF files from samples/ directory
- Real OpenAI API calls for NER extraction
- Real FDA/RxNorm/UNII API calls for enrichment

NOTE: These tests require:
- Docker running (for testcontainers)
- OPENAI_API_KEY environment variable set
- Internet access for external APIs
"""

from pathlib import Path
from typing import AsyncGenerator

import httpx
import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.exception_handler import register_exception_handlers
from src.api.middleware.logging import RequestLoggingMiddleware
from src.api.routes import extract, health
from src.container import Container

from tests.fixtures.containers import ArangoTestContainer


SAMPLES_DIR = Path(__file__).parent.parent.parent / "samples"


@pytest.mark.integration
class TestExtractRoutesRealRequests:
    """
    Integration tests for /extract endpoint with REAL API calls.
    
    These tests make actual requests to:
    - OpenAI API for NER extraction
    - FDA API for drug data
    - RxNorm API for drug info
    - UNII API for substance data
    """

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
        application.include_router(extract.router)

        return application

    @pytest.fixture
    async def client(self, app_with_db: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Create async test client."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_with_db),
            base_url="http://test",
            timeout=120.0,
        ) as client:
            yield client

    @pytest.fixture
    def sample_pdf_john_doe(self) -> bytes:
        """Load real sample PDF - John Doe resume (primary test file)."""
        pdf_path = SAMPLES_DIR / "Code_Challenge_Resume_1_-_John_Doe.pdf"
        if not pdf_path.exists():
            pytest.skip(f"Sample PDF not found: {pdf_path}")
        return pdf_path.read_bytes()

    # @pytest.fixture
    # def sample_pdf_jane_doe(self) -> bytes:
    #     """Load real sample PDF - Jane Doe resume."""
    #     pdf_path = SAMPLES_DIR / "Code_Challenge_Resume_2_-_Jane_Doe.pdf"
    #     if not pdf_path.exists():
    #         pytest.skip(f"Sample PDF not found: {pdf_path}")
    #     return pdf_path.read_bytes()

    # @pytest.fixture
    # def sample_pdf_jennifer_doe(self) -> bytes:
    #     """Load real sample PDF - Jennifer Doe resume."""
    #     pdf_path = SAMPLES_DIR / "Code_Challenge_Resume_3_-_Jennifer_Doe.pdf"
    #     if not pdf_path.exists():
    #         pytest.skip(f"Sample PDF not found: {pdf_path}")
    #     return pdf_path.read_bytes()

    async def test_extract_john_doe_resume_real_api(
        self,
        client: httpx.AsyncClient,
        sample_pdf_john_doe: bytes,
        container: Container,
    ) -> None:
        """
        Test POST /extract with John Doe resume using REAL API calls.
        
        This test:
        1. Uploads the real PDF file
        2. Extracts text from PDF (real)
        3. Calls OpenAI API for NER extraction (real)
        4. Enriches substances via FDA/RxNorm/UNII APIs (real)
        5. Persists results to ArangoDB (real via testcontainer)
        """
        response = await client.post(
            "/extract",
            files={
                "file": (
                    "Code_Challenge_Resume_1_-_John_Doe.pdf",
                    sample_pdf_john_doe,
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], dict)
        
        result = data["data"]
        assert "extraction_id" in result
        assert "entities" in result
        
        if result["entities"]:
            for entity in result["entities"]:
                assert "name" in entity
                assert "type" in entity

    async def test_extract_caching_works(
        self,
        client: httpx.AsyncClient,
        sample_pdf_john_doe: bytes,
        container: Container,
    ) -> None:
        """
        Test that extraction results are cached in ArangoDB.
        
        Second request with same PDF should return cached results
        without calling OpenAI API again.
        """
        response1 = await client.post(
            "/extract",
            files={
                "file": (
                    "cache_test.pdf",
                    sample_pdf_john_doe,
                    "application/pdf",
                )
            },
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["success"] is True

        response2 = await client.post(
            "/extract",
            files={
                "file": (
                    "cache_test.pdf",
                    sample_pdf_john_doe,
                    "application/pdf",
                )
            },
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["success"] is True

        assert data1["data"] == data2["data"]

    async def test_extract_substances_persisted_to_db(
        self,
        client: httpx.AsyncClient,
        sample_pdf_john_doe: bytes,
        container: Container,
    ) -> None:
        """
        Test that extracted substances are persisted to ArangoDB.
        
        After extraction, substances should be queryable from the database.
        """
        response = await client.post(
            "/extract",
            files={
                "file": (
                    "persistence_test.pdf",
                    sample_pdf_john_doe,
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        if data["data"] and data["data"]["entities"]:
            substance_repo = await container.get_substance_repository()
            
            for entity in data["data"]["entities"]:
                if entity.get("substance_id"):
                    substance_key = entity["substance_id"]
                    found = await substance_repo.find_by_key(substance_key)
                    
                    assert found is not None, f"Substance {substance_key} not found in DB"
                    assert found.name is not None

    async def test_extract_response_structure(
        self,
        client: httpx.AsyncClient,
        sample_pdf_john_doe: bytes,
        container: Container,
    ) -> None:
        """Test that /extract returns proper BaseResponse structure."""
        response = await client.post(
            "/extract",
            files={
                "file": (
                    "structure_test.pdf",
                    sample_pdf_john_doe,
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert "data" in data
        assert data["success"] is True
        assert isinstance(data["data"], dict)
        assert "extraction_id" in data["data"]
        assert "entities" in data["data"]

    # async def test_extract_jane_doe_resume_real_api(
    #     self,
    #     client: httpx.AsyncClient,
    #     sample_pdf_jane_doe: bytes,
    #     container: Container,
    # ) -> None:
    #     """Test POST /extract with Jane Doe resume using REAL API calls."""
    #     response = await client.post(
    #         "/extract",
    #         files={
    #             "file": (
    #                 "Code_Challenge_Resume_2_-_Jane_Doe.pdf",
    #                 sample_pdf_jane_doe,
    #                 "application/pdf",
    #             )
    #         },
    #     )
    #
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["success"] is True

    # async def test_extract_jennifer_doe_resume_real_api(
    #     self,
    #     client: httpx.AsyncClient,
    #     sample_pdf_jennifer_doe: bytes,
    #     container: Container,
    # ) -> None:
    #     """Test POST /extract with Jennifer Doe resume using REAL API calls."""
    #     response = await client.post(
    #         "/extract",
    #         files={
    #             "file": (
    #                 "Code_Challenge_Resume_3_-_Jennifer_Doe.pdf",
    #                 sample_pdf_jennifer_doe,
    #                 "application/pdf",
    #             )
    #         },
    #     )
    #
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["success"] is True
