"""
Drug Repository (Async).

Handles persistence of Drug entities to ArangoDB.
"""

from typing import ClassVar

from src.domain.entities.drug import Drug
from src.infrastructure.database.repositories.base import (
    BaseRepository,
    EdgeDefinition,
    IndexDefinition,
)
from src.shared.logging import get_logger

logger = get_logger(__name__)


class DrugRepository(BaseRepository[Drug]):
    """Async repository for Drug entities."""

    collection_name: ClassVar[str] = "drugs"

    indices: ClassVar[list[IndexDefinition]] = [
        IndexDefinition(fields=["application_number"], unique=False),
        IndexDefinition(fields=["brand_names[*]"], type="persistent"),
        IndexDefinition(fields=["generic_names[*]"], type="persistent"),
        IndexDefinition(fields=["rxcui[*]"], type="persistent"),
        IndexDefinition(fields=["is_enriched"], type="persistent"),
    ]

    edge_definitions: ClassVar[list[EdgeDefinition]] = [
        EdgeDefinition(
            collection="drug_has_substance",
            from_collections=["drugs"],
            to_collections=["substances"],
        ),
        EdgeDefinition(
            collection="drug_has_label",
            from_collections=["drugs"],
            to_collections=["drug_labels"],
        ),
        EdgeDefinition(
            collection="drug_in_class",
            from_collections=["drugs"],
            to_collections=["pharm_classes"],
        ),
    ]

    async def find_by_key(self, key: str) -> Drug | None:
        """Find drug by _key."""
        doc = await super().find_by_key(key)
        if doc:
            return Drug.from_dict(doc)
        return None

    async def find_by_name(self, name: str) -> Drug | None:
        """Find drug by brand or generic name."""
        query = """
        FOR d IN drugs
            FILTER LOWER(@name) IN (FOR n IN d.brand_names RETURN LOWER(n))
                OR LOWER(@name) IN (FOR n IN d.generic_names RETURN LOWER(n))
            LIMIT 1
            RETURN d
        """
        results = await self.execute_query(query, {"name": name})
        if results:
            return Drug.from_dict(results[0])
        return None

    async def find_by_rxcui(self, rxcui: str) -> Drug | None:
        """Find drug by RxCUI."""
        query = """
        FOR d IN drugs
            FILTER @rxcui IN d.rxcui
            LIMIT 1
            RETURN d
        """
        results = await self.execute_query(query, {"rxcui": rxcui})
        if results:
            return Drug.from_dict(results[0])
        return None

    async def find_by_application_number(self, app_number: str) -> Drug | None:
        """Find drug by FDA application number."""
        query = """
        FOR d IN drugs
            FILTER d.application_number == @app_number
            LIMIT 1
            RETURN d
        """
        results = await self.execute_query(query, {"app_number": app_number})
        if results:
            return Drug.from_dict(results[0])
        return None

    async def search(self, term: str, limit: int = 20) -> list[Drug]:
        """Search drugs by name (brand or generic)."""
        query = """
        FOR d IN drugs
            FILTER CONTAINS(LOWER(CONCAT_SEPARATOR(" ", d.brand_names)), LOWER(@term))
                OR CONTAINS(LOWER(CONCAT_SEPARATOR(" ", d.generic_names)), LOWER(@term))
            LIMIT @limit
            RETURN d
        """
        results = await self.execute_query(query, {"term": term, "limit": limit})
        return [Drug.from_dict(doc) for doc in results]

    async def save(self, drug: Drug) -> Drug:
        """Save or update a drug."""
        doc = await self.upsert(drug.to_dict())
        return Drug.from_dict(doc)

    async def find_unenriched(self, limit: int = 100) -> list[Drug]:
        """Find drugs that haven't been enriched yet."""
        query = """
        FOR d IN drugs
            FILTER d.is_enriched == false OR d.is_enriched == null
            LIMIT @limit
            RETURN d
        """
        results = await self.execute_query(query, {"limit": limit})
        return [Drug.from_dict(doc) for doc in results]

    async def find_enriched_by_name(self, name: str) -> Drug | None:
        """
        Find an enriched drug by brand or generic name (single lookup).

        Also checks for alias drugs and follows the alias edge.

        Args:
            name: Drug name to search

        Returns:
            Drug if found and enriched, None otherwise
        """
        query = """
        FOR d IN drugs
            FILTER d.is_enriched == true
            FILTER LOWER(@name) IN (FOR n IN d.brand_names RETURN LOWER(n))
                OR LOWER(@name) IN (FOR n IN d.generic_names RETURN LOWER(n))
            LIMIT 1
            RETURN d
        """
        results = await self.execute_query(query, {"name": name})
        if results:
            return Drug.from_dict(results[0])

        alias_drug = await self.find_by_alias(name)
        if alias_drug:
            return alias_drug

        return None

    async def find_enriched_by_names(self, names: list[str]) -> dict[str, Drug]:
        """
        Find enriched drugs by brand or generic names (bulk).

        Also checks for alias drugs and follows alias edges.

        Args:
            names: List of drug names to search

        Returns:
            Dict mapping lowercase name -> Drug (only enriched drugs)
        """
        if not names:
            return {}

        query = """
        FOR name IN @names
            LET direct_match = FIRST(
                FOR d IN drugs
                    FILTER d.is_enriched == true
                    FILTER LOWER(name) IN (FOR n IN d.brand_names RETURN LOWER(n))
                        OR LOWER(name) IN (FOR n IN d.generic_names RETURN LOWER(n))
                    LIMIT 1
                    RETURN d
            )
            LET alias_key = SUBSTITUTE(SUBSTITUTE(LOWER(name), " ", "_"), "-", "_")
            LET alias_match = FIRST(
                FOR alias IN drugs
                    FILTER alias._key == alias_key AND alias.is_alias == true
                    FOR target IN 1..1 OUTBOUND alias drug_alias_of
                        FILTER target.is_enriched == true
                        LIMIT 1
                        RETURN target
            )
            LET found_drug = direct_match != null ? direct_match : alias_match
            FILTER found_drug != null
            RETURN { search_name: name, drug: found_drug }
        """
        results = await self.execute_query(query, {"names": names})

        return {
            r["search_name"].lower(): Drug.from_dict(r["drug"])
            for r in results
        }

    async def find_by_alias(self, alias_name: str) -> Drug | None:
        """
        Find target drug via alias.

        Looks for a drug with is_alias=True matching the name,
        then follows drug_alias_of edge to find the target drug.
        """
        alias_key = alias_name.lower().replace(" ", "_").replace("-", "_")

        query = """
        FOR alias IN drugs
            FILTER alias._key == @alias_key AND alias.is_alias == true
            FOR target IN 1..1 OUTBOUND alias drug_alias_of
                FILTER target.is_enriched == true
                LIMIT 1
                RETURN target
        """
        results = await self.execute_query(query, {"alias_key": alias_key})
        if results:
            return Drug.from_dict(results[0])
        return None
