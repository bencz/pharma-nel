"""
Health check endpoints.
"""

from fastapi import APIRouter

from src.api.dependencies import ContainerDep, SettingsDep
from src.api.schemas.health import (
    DependencyStatus,
    HealthResponse,
    ReadinessResponse,
)
from src.api.services.health_checker import HealthChecker

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the API is running and healthy. Includes dependency status.",
)
async def health_check(settings: SettingsDep, container: ContainerDep) -> HealthResponse:
    checker = HealthChecker(settings, container.arango_connection)
    dependencies = await checker.check_all()

    all_healthy = all(
        d.status in (DependencyStatus.HEALTHY, DependencyStatus.NOT_CONFIGURED)
        for d in dependencies
    )

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        dependencies=dependencies,
    )


@router.get(
    "/health/live",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Simple liveness check - returns healthy if the API is running.",
)
async def liveness_check(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    description="Check if the API is ready to accept requests (all dependencies healthy).",
)
async def readiness_check(settings: SettingsDep, container: ContainerDep) -> ReadinessResponse:
    checker = HealthChecker(settings, container.arango_connection)
    dependencies = await checker.check_all()

    checks = {
        d.name: d.status in (DependencyStatus.HEALTHY, DependencyStatus.NOT_CONFIGURED)
        for d in dependencies
    }

    return ReadinessResponse(
        ready=all(checks.values()) if checks else True,
        checks=checks,
    )
