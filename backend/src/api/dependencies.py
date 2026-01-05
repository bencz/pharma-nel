"""
FastAPI Dependencies.

Provides dependency injection for routes.
"""

from typing import Annotated

from fastapi import Depends

from src.container import Container, get_container
from src.infrastructure.clients.fda_client import FDAClient
from src.infrastructure.clients.rxnorm_client import RxNormClient
from src.infrastructure.clients.unii_client import UNIIClient
from src.shared.config import Settings


def get_settings(container: Annotated[Container, Depends(get_container)]) -> Settings:
    return container.settings


def get_fda_client(container: Annotated[Container, Depends(get_container)]) -> FDAClient:
    return container.fda_client


def get_rxnorm_client(container: Annotated[Container, Depends(get_container)]) -> RxNormClient:
    return container.rxnorm_client


def get_unii_client(container: Annotated[Container, Depends(get_container)]) -> UNIIClient:
    return container.unii_client


ContainerDep = Annotated[Container, Depends(get_container)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
FDAClientDep = Annotated[FDAClient, Depends(get_fda_client)]
RxNormClientDep = Annotated[RxNormClient, Depends(get_rxnorm_client)]
UNIIClientDep = Annotated[UNIIClient, Depends(get_unii_client)]
