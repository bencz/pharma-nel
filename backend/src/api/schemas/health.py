"""
Health check schemas with detailed dependency status.
"""

from enum import Enum

from pydantic import BaseModel, Field


class DependencyStatus(str, Enum):
    """Status of a dependency."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    NOT_CONFIGURED = "not_configured"


class DependencyHealth(BaseModel):
    """Health status of a single dependency."""

    name: str
    status: DependencyStatus
    latency_ms: float | None = None
    message: str | None = None


class HealthResponse(BaseModel):
    """Detailed health check response."""

    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    dependencies: list[DependencyHealth] = Field(
        default_factory=list,
        description="Health status of each dependency",
    )

    @property
    def is_healthy(self) -> bool:
        if not self.dependencies:
            return self.status == "healthy"
        return all(
            d.status in (DependencyStatus.HEALTHY, DependencyStatus.NOT_CONFIGURED)
            for d in self.dependencies
        )


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    ready: bool
    checks: dict[str, bool] = Field(default_factory=dict)
