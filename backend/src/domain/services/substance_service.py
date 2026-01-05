"""
Substance Service.

Main service for substance operations. Handles fetching substance data
with all related entities from the knowledge graph.
"""

from typing import Any

from src.domain.entities.pharma_graph import SubstanceGraphData
from src.domain.entities.substance import Substance
from src.domain.exceptions.drug import SubstanceNotFoundError
from src.domain.services.substance_enrichment_service import SubstanceEnrichmentService
from src.infrastructure.database.repositories.openfda_graph_repository import OpenFDAGraphRepository
from src.infrastructure.database.repositories.substance_repository import SubstanceRepository
from src.shared.logging import get_logger

logger = get_logger(__name__)


class SubstanceService:
    """
    Service for substance operations.

    Handles:
    - Fetching substances from repository
    - Getting substance with all related data (graph traversal)
    - Enriching substances with FDA/RxNorm/UNII data
    """

    def __init__(
        self,
        substance_repository: SubstanceRepository,
        graph_repository: OpenFDAGraphRepository,
        enrichment_service: SubstanceEnrichmentService | None = None,
    ) -> None:
        self._substance_repo = substance_repository
        self._graph_repo = graph_repository
        self._enrichment = enrichment_service

    async def get_by_key(self, key: str) -> Substance:
        """
        Get substance by key.

        Args:
            key: Substance document key

        Returns:
            Substance entity

        Raises:
            SubstanceNotFoundError: If substance not found
        """
        substance = await self._substance_repo.find_by_key(key)

        if not substance:
            substance = await self._substance_repo.find_by_name(key)

        if not substance:
            raise SubstanceNotFoundError(substance_id=key)

        return substance

    async def get_by_name(self, name: str) -> Substance:
        """
        Get substance by name.

        Args:
            name: Substance name to search

        Returns:
            Substance entity

        Raises:
            SubstanceNotFoundError: If substance not found
        """
        substance = await self._substance_repo.find_by_name(name)

        if not substance:
            substance = await self._substance_repo.find_by_key(
                name.lower().replace(" ", "_").replace("-", "_")
            )

        if not substance:
            raise SubstanceNotFoundError(substance_id=name)

        return substance

    async def get_profile(self, substance_id: str) -> dict[str, Any]:
        """
        Get complete substance profile with all related data.

        Args:
            substance_id: Substance key or name

        Returns:
            Dict with substance data and all relations

        Raises:
            SubstanceNotFoundError: If substance not found
        """
        substance = await self._substance_repo.find_by_key(substance_id)

        if not substance:
            substance = await self._substance_repo.find_by_name(substance_id)

        if not substance:
            raise SubstanceNotFoundError(substance_id=substance_id)

        logger.info("substance_profile_lookup", key=substance.key, name=substance.name)

        relations = await self._graph_repo.get_substance_relations(substance.key)

        return {
            "substance": substance,
            "relations": relations,
        }

    async def search(self, term: str, limit: int = 20) -> list[Substance]:
        """
        Search substances by name.

        Args:
            term: Search term
            limit: Maximum results

        Returns:
            List of matching substances
        """
        return await self._substance_repo.search(term, limit=limit)

    async def enrich_substance(self, name: str, force: bool = False) -> SubstanceGraphData:
        """
        Enrich a substance by name, checking for existing enriched data first.

        Args:
            name: Substance name to enrich
            force: If True, re-enrich even if already exists

        Returns:
            SubstanceGraphData with enrichment results
        """
        if not self._enrichment:
            raise RuntimeError("SubstanceService requires enrichment_service for enrichment")

        if not force:
            existing = await self._substance_repo.find_enriched_by_name(name)
            if existing:
                logger.info(
                    "substance_already_enriched",
                    search_term=name,
                    substance_key=existing.key,
                )
                return SubstanceGraphData(
                    search_term=name,
                    found=True,
                    substances={existing.key: existing},
                )

        return await self._enrich_and_persist(name)

    async def _enrich_and_persist(self, search_term: str) -> SubstanceGraphData:
        """Enrich substance data and persist to graph."""
        logger.info("substance_enrichment_triggered", search_term=search_term)

        graph_data = await self._enrichment.get_substance_data(
            search_term,
            include_events=False,
            events_limit=0,
            include_interactions=True,
        )

        if graph_data.found:
            counts = await self._graph_repo.persist_graph_data(graph_data)
            logger.info(
                "substance_enrichment_persisted",
                search_term=search_term,
                counts=counts,
            )
        else:
            logger.warning("substance_enrichment_not_found", search_term=search_term)

        return graph_data

    async def find_enriched_by_names(self, names: list[str]) -> dict[str, Substance]:
        """Find enriched substances by names (bulk)."""
        return await self._substance_repo.find_enriched_by_names(names)
