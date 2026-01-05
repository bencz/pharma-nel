"""
OpenFDA API Client.

Endpoints:
- drug/drugsfda: Drug approval data
- drug/label: Drug labeling/package inserts
- drug/ndc: National Drug Code Directory
- drug/event: Adverse events
- drug/enforcement: Drug recalls
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from src.infrastructure.clients.base import BaseHTTPClient
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class FDAClientConfig:
    """FDA API client configuration."""

    base_url: str = "https://api.fda.gov"
    api_key: str | None = None
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True


class FDAClient(BaseHTTPClient):
    """Async client for OpenFDA API."""

    ENDPOINTS = {
        "drugsfda": "/drug/drugsfda.json",
        "label": "/drug/label.json",
        "ndc": "/drug/ndc.json",
        "event": "/drug/event.json",
        "enforcement": "/drug/enforcement.json",
    }

    def __init__(self, config: FDAClientConfig | None = None) -> None:
        config = config or FDAClientConfig()
        super().__init__(
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
            verify_ssl=config.verify_ssl,
        )
        self._api_key = config.api_key

    def _build_search_query(self, drug_name: str, field: str | None = None) -> str:
        escaped_name = drug_name.replace('"', '\\"')
        if field:
            return f'{field}:"{escaped_name}"'
        return (
            f'openfda.brand_name:"{escaped_name}" OR '
            f'openfda.generic_name:"{escaped_name}" OR '
            f'openfda.substance_name:"{escaped_name}"'
        )

    async def _fda_request(
        self,
        endpoint: str,
        params: dict[str, Any],
    ) -> dict[str, Any] | None:
        if self._api_key:
            params["api_key"] = self._api_key

        response = await self.get(endpoint, params=params)

        if response.status_code == 404:
            return None
        if response.status_code == 200:
            return response.json()

        logger.warning(
            "fda_api_error",
            endpoint=endpoint,
            status_code=response.status_code,
        )
        return None

    async def search_drugsfda(self, drug_name: str, limit: int = 100) -> list[dict[str, Any]]:
        params = {
            "search": self._build_search_query(drug_name),
            "limit": min(limit, 1000),
        }
        result = await self._fda_request(self.ENDPOINTS["drugsfda"], params)
        return result.get("results", []) if result else []

    async def search_labels(self, drug_name: str, limit: int = 100) -> list[dict[str, Any]]:
        params = {
            "search": self._build_search_query(drug_name),
            "limit": min(limit, 100),
        }
        result = await self._fda_request(self.ENDPOINTS["label"], params)
        return result.get("results", []) if result else []

    async def get_label_by_spl_id(self, spl_id: str) -> dict[str, Any] | None:
        """Get a specific drug label by its SPL ID."""
        params = {"search": f'openfda.spl_id:"{spl_id}"', "limit": 1}
        result = await self._fda_request(self.ENDPOINTS["label"], params)
        results = result.get("results", []) if result else []
        return results[0] if results else None

    async def search_ndc(self, drug_name: str, limit: int = 100) -> list[dict[str, Any]]:
        escaped_name = drug_name.replace('"', '\\"')
        search_query = (
            f'brand_name:"{escaped_name}" OR '
            f'generic_name:"{escaped_name}" OR '
            f'active_ingredients.name:"{escaped_name}"'
        )
        params = {"search": search_query, "limit": min(limit, 100)}
        result = await self._fda_request(self.ENDPOINTS["ndc"], params)
        return result.get("results", []) if result else []

    async def search_adverse_events(
        self,
        drug_name: str,
        limit: int = 100,
        serious: bool | None = None,
    ) -> list[dict[str, Any]]:
        escaped_name = drug_name.replace('"', '\\"')
        search_parts = [
            f'(patient.drug.openfda.brand_name:"{escaped_name}" OR '
            f'patient.drug.openfda.generic_name:"{escaped_name}" OR '
            f'patient.drug.medicinalproduct:"{escaped_name}")'
        ]
        if serious is not None:
            search_parts.append(f"serious:{1 if serious else 2}")

        params = {"search": " AND ".join(search_parts), "limit": min(limit, 100)}
        result = await self._fda_request(self.ENDPOINTS["event"], params)
        return result.get("results", []) if result else []

    async def search_enforcement(self, drug_name: str, limit: int = 100) -> list[dict[str, Any]]:
        params = {
            "search": self._build_search_query(drug_name),
            "limit": min(limit, 100),
        }
        result = await self._fda_request(self.ENDPOINTS["enforcement"], params)
        return result.get("results", []) if result else []

    async def get_all_drug_data(
        self,
        drug_name: str,
        include_events: bool = True,
        events_limit: int = 100,
    ) -> dict[str, list[dict[str, Any]]]:
        tasks = [
            self.search_drugsfda(drug_name),
            self.search_ndc(drug_name),
            self.search_enforcement(drug_name),
        ]

        if include_events:
            tasks.append(self.search_adverse_events(drug_name, limit=events_limit))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        data = {
            "drugsfda": results[0] if not isinstance(results[0], Exception) else [],
            "ndc": results[1] if not isinstance(results[1], Exception) else [],
            "enforcement": results[2] if not isinstance(results[2], Exception) else [],
        }

        if include_events:
            data["events"] = results[3] if not isinstance(results[3], Exception) else []

        return data
