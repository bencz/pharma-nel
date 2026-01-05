"""
Testcontainers fixtures for integration tests.

Provides Docker containers for ArangoDB  during tests.
"""

import time
from typing import AsyncGenerator, Generator

import pytest
from testcontainers.core.container import DockerContainer

from src.infrastructure.database.connection import ArangoConnection
from src.shared.config import Settings


class ArangoTestContainer:
    """
    Custom ArangoDB test container using the new testcontainers API.
    
    Avoids deprecation warnings from the built-in ArangoDbContainer.
    """

    ARANGO_PORT = 8529
    ARANGO_PASSWORD = "test_password"

    def __init__(self) -> None:
        self._container: DockerContainer | None = None
        self._host: str = ""
        self._port: int = self.ARANGO_PORT

    def start(self) -> "ArangoTestContainer":
        self._container = DockerContainer(image="arangodb:latest")
        self._container.with_exposed_ports(self.ARANGO_PORT)
        self._container.with_env("ARANGO_ROOT_PASSWORD", self.ARANGO_PASSWORD)
        self._container.start()

        self._host = self._container.get_container_host_ip()
        self._port = int(self._container.get_exposed_port(self.ARANGO_PORT))

        self._wait_for_ready()

        return self

    def _wait_for_ready(self, timeout: int = 120) -> None:
        """Wait for ArangoDB to be ready to accept connections."""
        import httpx

        url = f"{self.url}/_api/version"
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = httpx.get(
                    url,
                    timeout=5.0,
                    auth=("root", self.ARANGO_PASSWORD),
                )
                if response.status_code in (200, 401):
                    time.sleep(1)
                    return
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ReadError):
                pass
            time.sleep(1)

        raise TimeoutError(f"ArangoDB did not become ready within {timeout} seconds")

    def stop(self) -> None:
        if self._container:
            self._container.stop()
            self._container = None

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self._port}"

    def get_settings(self) -> Settings:
        return Settings(
            environment="test",
            debug=True,
            log_level="DEBUG",
            log_json=False,
            http_verify_ssl=False,
            arango_host=self.url,
            arango_database="_system",
            arango_user="root",
            arango_password=self.ARANGO_PASSWORD,
        )


@pytest.fixture(scope="session")
def arango_container() -> Generator[ArangoTestContainer, None, None]:
    """
    Session-scoped ArangoDB container.

    Starts once per test session and is shared across all tests.
    """
    container = ArangoTestContainer()
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def test_settings_with_arango(arango_container: ArangoTestContainer) -> Settings:
    """Test settings configured to use the ArangoDB container."""
    return arango_container.get_settings()


@pytest.fixture
async def arango_connection(
    test_settings_with_arango: Settings,
) -> AsyncGenerator[ArangoConnection, None]:
    """
    Async fixture for ArangoDB connection.

    Creates a fresh connection for each test.
    """
    connection = ArangoConnection(test_settings_with_arango)
    yield connection
    await connection.close()


@pytest.fixture
async def arango_db(arango_connection: ArangoConnection):
    """Get the database instance from connection."""
    return await arango_connection.get_db()
