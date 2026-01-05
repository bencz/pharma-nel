"""
Health Checker Service.

Checks connectivity to all dependencies (ArangoDB, etc).
"""

import time

from src.api.schemas.health import DependencyHealth, DependencyStatus
from src.infrastructure.database.connection import ArangoConnection
from src.shared.config import Settings
from src.shared.logging import get_logger

logger = get_logger(__name__)


class HealthChecker:
    """Service to check health of all dependencies."""

    def __init__(
        self,
        settings: Settings,
        arango_connection: ArangoConnection | None = None,
    ) -> None:
        self._settings = settings
        self._arango_connection = arango_connection

    async def check_all(self) -> list[DependencyHealth]:
        """Check health of all configured dependencies."""
        checks: list[DependencyHealth] = []

        checks.append(await self.check_arangodb())

        return checks

    async def check_arangodb(self) -> DependencyHealth:
        """Check ArangoDB connectivity using the connection from Container."""
        start = time.perf_counter()

        try:
            if self._arango_connection:
                health = await self._arango_connection.health_check()
                latency = (time.perf_counter() - start) * 1000

                if health.get("healthy"):
                    return DependencyHealth(
                        name="arangodb",
                        status=DependencyStatus.HEALTHY,
                        latency_ms=round(latency, 2),
                        message=f"Connected to ArangoDB {health.get('version')}"
                    )
                else:
                    return DependencyHealth(
                        name="arangodb",
                        status=DependencyStatus.UNHEALTHY,
                        latency_ms=round(latency, 2),
                        message=f"Connection failed: {health.get('error')}"
                    )
            else:
                return DependencyHealth(
                    name="arangodb",
                    status=DependencyStatus.NOT_CONFIGURED,
                    message="ArangoDB connection not available",
                )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.warning("arangodb_health_check", status="unhealthy", error=str(e))

            return DependencyHealth(
                name="arangodb",
                status=DependencyStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                message=f"Connection failed: {e}"
            )
