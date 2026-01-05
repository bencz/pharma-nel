"""
RxNorm API Client.

RxNorm provides standardized nomenclature for medications and relationships
between different drug names/codes.

Documentation: https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from src.infrastructure.clients.base import BaseHTTPClient
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class RxNormClientConfig:
    """RxNorm API client configuration."""

    base_url: str = "https://rxnav.nlm.nih.gov/REST"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True


class RxNormClient(BaseHTTPClient):
    """Async client for RxNorm API."""

    def __init__(self, config: RxNormClientConfig | None = None) -> None:
        config = config or RxNormClientConfig()
        super().__init__(
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
            verify_ssl=config.verify_ssl,
        )

    async def _rxnorm_request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        params = params or {}
        params["format"] = "json"

        response = await self.get(endpoint, params=params)

        if response.status_code == 404:
            return None
        if response.status_code == 200:
            return response.json()

        logger.warning(
            "rxnorm_api_error",
            endpoint=endpoint,
            status_code=response.status_code,
        )
        return None

    async def get_rxcui_by_name(self, drug_name: str) -> list[dict[str, Any]]:
        result = await self._rxnorm_request("/rxcui.json", {"name": drug_name})
        if result and "idGroup" in result:
            rxnorm_ids = result["idGroup"].get("rxnormId", [])
            if rxnorm_ids:
                return [{"rxcui": rxcui, "name": drug_name} for rxcui in rxnorm_ids]
        return []

    async def approximate_match(self, drug_name: str, max_entries: int = 10) -> list[dict[str, Any]]:
        result = await self._rxnorm_request(
            "/approximateTerm.json",
            {"term": drug_name, "maxEntries": max_entries},
        )
        if result and "approximateGroup" in result:
            candidates = result["approximateGroup"].get("candidate", [])
            return [
                {
                    "rxcui": c.get("rxcui"),
                    "name": c.get("name"),
                    "score": c.get("score"),
                    "rank": c.get("rank"),
                }
                for c in candidates
            ]
        return []

    async def get_drug_info(self, rxcui: str) -> dict[str, Any] | None:
        result = await self._rxnorm_request(f"/rxcui/{rxcui}/properties.json")
        if result and "properties" in result:
            return result["properties"]
        return None

    async def get_related_drugs(self, rxcui: str) -> dict[str, list[dict[str, Any]]]:
        result = await self._rxnorm_request(f"/rxcui/{rxcui}/allrelated.json")
        relationships: dict[str, list[dict[str, Any]]] = {}

        if result and "allRelatedGroup" in result:
            concept_groups = result["allRelatedGroup"].get("conceptGroup", [])
            for group in concept_groups:
                tty = group.get("tty", "unknown")
                concepts = group.get("conceptProperties", [])
                if concepts:
                    relationships[tty] = [
                        {
                            "rxcui": c.get("rxcui"),
                            "name": c.get("name"),
                            "synonym": c.get("synonym"),
                            "tty": c.get("tty"),
                        }
                        for c in concepts
                    ]
        return relationships

    async def get_ndc_codes(self, rxcui: str) -> list[str]:
        result = await self._rxnorm_request(f"/rxcui/{rxcui}/ndcs.json")
        if result and "ndcGroup" in result:
            ndc_list = result["ndcGroup"].get("ndcList", {})
            return ndc_list.get("ndc", [])
        return []

    async def get_drug_interactions(self, rxcui: str) -> list[dict[str, Any]]:
        result = await self._rxnorm_request("/interaction/interaction.json", {"rxcui": rxcui})
        interactions: list[dict[str, Any]] = []

        if result and isinstance(result, dict) and "interactionTypeGroup" in result:
            for type_group in result["interactionTypeGroup"]:
                for interaction_type in type_group.get("interactionType", []):
                    for pair in interaction_type.get("interactionPair", []):
                        interactions.append({
                            "severity": pair.get("severity"),
                            "description": pair.get("description"),
                            "interacting_drugs": [
                                {
                                    "rxcui": c.get("minConceptItem", {}).get("rxcui"),
                                    "name": c.get("minConceptItem", {}).get("name"),
                                }
                                for c in pair.get("interactionConcept", [])
                            ],
                        })
        return interactions

    async def get_spelling_suggestions(self, drug_name: str) -> list[str]:
        result = await self._rxnorm_request("/spellingsuggestions.json", {"name": drug_name})
        if result and "suggestionGroup" in result:
            suggestion_list = result["suggestionGroup"].get("suggestionList", {})
            return suggestion_list.get("suggestion", [])
        return []

    async def get_all_drug_data(
        self,
        drug_name: str,
        rxcui_hint: str | None = None,
    ) -> dict[str, Any]:
        primary_rxcui = rxcui_hint
        rxcuis: list[dict[str, Any]] = []

        if not primary_rxcui:
            rxcuis = await self.get_rxcui_by_name(drug_name)
            if not rxcuis:
                approx = await self.approximate_match(drug_name, max_entries=5)
                if approx:
                    rxcuis = [{"rxcui": approx[0]["rxcui"], "name": approx[0]["name"]}]

            if not rxcuis:
                return {
                    "found": False,
                    "search_term": drug_name,
                    "suggestions": await self.get_spelling_suggestions(drug_name),
                }
            primary_rxcui = rxcuis[0]["rxcui"]
        else:
            rxcuis = [{"rxcui": primary_rxcui, "name": drug_name}]

        tasks = [
            self.get_drug_info(primary_rxcui),
            self.get_related_drugs(primary_rxcui),
            self.get_ndc_codes(primary_rxcui),
            self.get_drug_interactions(primary_rxcui),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        info = results[0] if not isinstance(results[0], Exception) else None
        related = results[1] if not isinstance(results[1], Exception) else {}
        ndc_codes = results[2] if not isinstance(results[2], Exception) else []
        interactions = results[3] if not isinstance(results[3], Exception) else []

        ingredient_types = {"IN", "PIN", "MIN"}
        brand_types = {"BN", "SBDC", "SBD", "SBDF", "SBDG"}

        ingredients: list[dict[str, Any]] = []
        brands: list[dict[str, Any]] = []
        for tty, concepts in related.items():
            if tty in ingredient_types:
                ingredients.extend(concepts)
            elif tty in brand_types:
                brands.extend(concepts)

        return {
            "found": True,
            "search_term": drug_name,
            "rxcui": primary_rxcui,
            "all_rxcuis": rxcuis,
            "info": info,
            "ingredients": ingredients,
            "brands": brands,
            "ndc_codes": ndc_codes,
            "interactions": interactions,
            "related": related,
        }
