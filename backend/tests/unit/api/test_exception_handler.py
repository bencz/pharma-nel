"""
Unit tests for exception handlers.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.decorators import error_message
from src.api.middleware.exception_handler import register_exception_handlers
from src.api.schemas.base import BaseResponse
from src.domain.exceptions.base import DomainException
from src.domain.exceptions.drug import DrugNotFoundError
from src.infrastructure.exceptions.client import ClientException
from src.infrastructure.exceptions.database import DatabaseException


class TestExceptionHandlers:
    """Unit tests for global exception handlers."""

    @pytest.fixture
    def app(self) -> FastAPI:
        app = FastAPI()
        register_exception_handlers(app)
        return app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        return TestClient(app, raise_server_exceptions=False)

    def test_domain_exception_returns_correct_status(
        self, app: FastAPI, client: TestClient
    ) -> None:
        @app.get("/domain-error")
        async def raise_domain_error():
            raise DrugNotFoundError(drug_id="test-123")

        response = client.get("/domain-error")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "DRUG_NOT_FOUND"
        assert "test-123" in data["error"]["message"]

    def test_database_exception_returns_500(
        self, app: FastAPI, client: TestClient
    ) -> None:
        @app.get("/db-error")
        async def raise_db_error():
            raise DatabaseException(message="Connection failed")

        response = client.get("/db-error")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "DATABASE_ERROR"

    def test_client_exception_returns_502(
        self, app: FastAPI, client: TestClient
    ) -> None:
        @app.get("/client-error")
        async def raise_client_error():
            raise ClientException(message="External API failed")

        response = client.get("/client-error")

        assert response.status_code == 502
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "EXTERNAL_SERVICE_ERROR"

    def test_generic_exception_returns_default_message(
        self, app: FastAPI, client: TestClient
    ) -> None:
        @app.get("/generic-error")
        async def raise_generic_error():
            raise ValueError("Internal error details")

        response = client.get("/generic-error")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert "Internal error details" not in data["error"]["message"]

    def test_generic_exception_uses_custom_error_message(
        self, app: FastAPI, client: TestClient
    ) -> None:
        @app.post("/extract")
        @error_message("An error occurred while processing your document.")
        async def extract_with_error():
            raise RuntimeError("Unexpected internal error")

        response = client.post("/extract")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert data["error"]["message"] == "An error occurred while processing your document."

    def test_generic_exception_without_decorator_uses_default(
        self, app: FastAPI, client: TestClient
    ) -> None:
        @app.get("/no-decorator")
        async def no_decorator_error():
            raise RuntimeError("Some error")

        response = client.get("/no-decorator")

        assert response.status_code == 500
        data = response.json()
        assert data["error"]["message"] == "An unexpected error occurred. Please try again later."


class TestDomainExceptionDetails:
    """Tests for domain exception details propagation."""

    @pytest.fixture
    def app(self) -> FastAPI:
        app = FastAPI()
        register_exception_handlers(app)
        return app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        return TestClient(app, raise_server_exceptions=False)

    def test_exception_details_included(
        self, app: FastAPI, client: TestClient
    ) -> None:
        @app.get("/with-details")
        async def raise_with_details():
            raise DomainException(
                message="Custom error",
                details={"field": "name", "reason": "invalid"},
            )

        response = client.get("/with-details")

        data = response.json()
        assert data["error"]["details"]["field"] == "name"
        assert data["error"]["details"]["reason"] == "invalid"
