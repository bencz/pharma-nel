"""
Drug Service.

Service for drug (commercial product) operations.
For substance enrichment, use SubstanceService instead.
"""

from src.domain.entities.drug import Drug
from src.domain.exceptions.drug import DrugNotFoundError
from src.infrastructure.database.repositories.drug_repository import DrugRepository
from src.infrastructure.database.repositories.openfda_graph_repository import OpenFDAGraphRepository
from src.shared.logging import get_logger

logger = get_logger(__name__)


class DrugService:
    """
    Service for drug (commercial product) operations.

    Handles:
    - Fetching drugs from repository
    - Searching drugs by name/key/rxcui
    - Getting drug with graph relations
    """

    def __init__(
        self,
        drug_repository: DrugRepository,
        graph_repository: OpenFDAGraphRepository,
    ) -> None:
        self._drug_repo = drug_repository
        self._graph_repo = graph_repository

    async def get_by_key(self, key: str) -> Drug:
        """
        Get drug by key.

        Args:
            key: Drug document key

        Returns:
            Drug entity

        Raises:
            DrugNotFoundError: If drug not found
        """
        drug = await self._drug_repo.find_by_key(key)
        if not drug:
            raise DrugNotFoundError(key)
        return drug

    async def get_by_name(self, name: str) -> Drug:
        """
        Get drug by name (brand or generic).

        Args:
            name: Drug name to search

        Returns:
            Drug entity

        Raises:
            DrugNotFoundError: If drug not found
        """
        drug = await self._drug_repo.find_by_name(name)
        if not drug:
            raise DrugNotFoundError(name)
        return drug

    async def get_by_rxcui(self, rxcui: str) -> Drug:
        """Get drug by RxCUI."""
        drug = await self._drug_repo.find_by_rxcui(rxcui)
        if not drug:
            raise DrugNotFoundError(rxcui)
        return drug

    async def search(self, term: str, limit: int = 20) -> list[Drug]:
        """Search drugs by name."""
        return await self._drug_repo.search(term, limit)

    async def get_with_relations(self, key: str) -> dict | None:
        """Get drug with all related entities from graph."""
        return await self._graph_repo.get_drug_with_relations(key)
