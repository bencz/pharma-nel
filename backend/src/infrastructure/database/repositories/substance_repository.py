"""
Substance Repository (Async).

Handles persistence of Substance entities to ArangoDB.
"""

from typing import ClassVar

from src.domain.entities.substance import Substance
from src.infrastructure.database.repositories.base import (
    BaseRepository,
    IndexDefinition,
)
from src.shared.logging import get_logger

logger = get_logger(__name__)


class SubstanceRepository(BaseRepository[Substance]):
    """Async repository for Substance entities."""

    collection_name: ClassVar[str] = "substances"

    indices: ClassVar[list[IndexDefinition]] = [
        IndexDefinition(fields=["name"], type="persistent"),
        IndexDefinition(fields=["unii"], sparse=True),
        IndexDefinition(fields=["rxcui"], sparse=True),
        IndexDefinition(fields=["cas_number"], sparse=True),
        IndexDefinition(fields=["is_enriched"], type="persistent"),
    ]

    async def find_by_key(self, key: str) -> Substance | None:
        doc = await super().find_by_key(key)
        if doc:
            return Substance.from_dict(doc)
        return None

    async def find_by_unii(self, unii: str) -> Substance | None:
        query = """
        FOR s IN substances
            FILTER s.unii == @unii
            LIMIT 1
            RETURN s
        """
        results = await self.execute_query(query, {"unii": unii})
        if results:
            return Substance.from_dict(results[0])
        return None

    async def find_by_name(self, name: str) -> Substance | None:
        query = """
        FOR s IN substances
            FILTER LOWER(s.name) == LOWER(@name)
            LIMIT 1
            RETURN s
        """
        results = await self.execute_query(query, {"name": name})
        if results:
            return Substance.from_dict(results[0])
        return None

    async def search(self, term: str, limit: int = 20) -> list[Substance]:
        query = """
        FOR s IN substances
            FILTER CONTAINS(LOWER(s.name), LOWER(@term))
            LIMIT @limit
            RETURN s
        """
        results = await self.execute_query(query, {"term": term, "limit": limit})
        return [Substance.from_dict(doc) for doc in results]

    async def save(self, substance: Substance) -> Substance:
        doc = await self.upsert(substance.to_dict())
        return Substance.from_dict(doc)

    async def save_many(self, substances: list[Substance]) -> int:
        count = 0
        for substance in substances:
            await self.upsert(substance.to_dict())
            count += 1
        return count

    async def find_unenriched(self, limit: int = 100) -> list[Substance]:
        query = """
        FOR s IN substances
            FILTER s.is_enriched == false OR s.is_enriched == null
            LIMIT @limit
            RETURN s
        """
        results = await self.execute_query(query, {"limit": limit})
        return [Substance.from_dict(doc) for doc in results]

    async def find_enriched_by_name(self, name: str) -> Substance | None:
        """
        Find an enriched substance by name.

        Args:
            name: Substance name to search

        Returns:
            Substance if found and enriched, None otherwise
        """
        name_key = name.lower().replace(" ", "_").replace("-", "_")

        query = """
        FOR s IN substances
            FILTER s.is_enriched == true
            FILTER s._key == @name_key OR LOWER(s.name) == LOWER(@name)
            LIMIT 1
            RETURN s
        """
        results = await self.execute_query(query, {"name": name, "name_key": name_key})
        if results:
            return Substance.from_dict(results[0])
        return None

    async def find_enriched_by_names(self, names: list[str]) -> dict[str, Substance]:
        """
        Find enriched substances by names (bulk).

        Args:
            names: List of substance names to search

        Returns:
            Dict mapping lowercase name -> Substance (only enriched substances)
        """
        if not names:
            return {}

        names_lower = [n.lower() for n in names]
        keys = [n.lower().replace(" ", "_").replace("-", "_") for n in names]

        query = """
        FOR s IN substances
            FILTER s.is_enriched == true
            FILTER s._key IN @keys OR LOWER(s.name) IN @names_lower
            RETURN s
        """
        results = await self.execute_query(query, {"keys": keys, "names_lower": names_lower})

        found: dict[str, Substance] = {}
        for doc in results:
            substance = Substance.from_dict(doc)
            found[substance.name.lower()] = substance
            key_as_name = substance.key.replace("_", " ")
            if key_as_name not in found:
                found[key_as_name] = substance

        return found
