"""
Profile Repository (Async).

Handles persistence of user profiles extracted from resumes to ArangoDB.
Includes edge management for profile relationships.
"""

import hashlib
from typing import Any, ClassVar

from arangoasync.exceptions import DocumentInsertError
from arangoasync.typings import CollectionType

from src.domain.entities.profile import Profile
from src.infrastructure.database.repositories.base import (
    BaseRepository,
    IndexDefinition,
)
from src.shared.logging import get_logger

logger = get_logger(__name__)

PROFILE_EDGE_COLLECTIONS = [
    "profile_has_extraction",
    "profile_interested_in_substance",
]


class ProfileRepository(BaseRepository[Profile]):
    """Async repository for user profiles."""

    collection_name: ClassVar[str] = "profiles"

    indices: ClassVar[list[IndexDefinition]] = [
        IndexDefinition(fields=["email"], unique=True, sparse=True),
        IndexDefinition(fields=["full_name"], type="persistent"),
        IndexDefinition(fields=["linkedin"], unique=True, sparse=True),
        IndexDefinition(fields=["created_at"], type="persistent"),
    ]

    async def save_profile(self, profile: Profile) -> Profile:
        """
        Save or merge profile.

        If profile with same key exists, merge data preserving existing info.
        """
        existing_doc = await self.find_by_key(profile.key)

        if existing_doc:
            existing = Profile.from_dict(existing_doc)
            merged = existing.merge_with(profile)
            doc = merged.to_dict()
            await self.upsert(doc)
            logger.debug(
                "profile_merged",
                key=profile.key,
                extractions=len(merged.source_extractions),
            )
            return merged

        doc = profile.to_dict()
        await self.upsert(doc)
        logger.debug("profile_created", key=profile.key)
        return profile

    async def find_by_email(self, email: str) -> Profile | None:
        """Find profile by email."""
        query = """
        FOR p IN profiles
            FILTER p.email == @email
            LIMIT 1
            RETURN p
        """
        results = await self.execute_query(query, {"email": email.lower().strip()})
        return Profile.from_dict(results[0]) if results else None

    async def find_by_name(self, full_name: str) -> Profile | None:
        """Find profile by full name (case-insensitive)."""
        query = """
        FOR p IN profiles
            FILTER LOWER(p.full_name) == LOWER(@full_name)
            LIMIT 1
            RETURN p
        """
        results = await self.execute_query(query, {"full_name": full_name})
        return Profile.from_dict(results[0]) if results else None

    async def find_by_linkedin(self, linkedin: str) -> Profile | None:
        """Find profile by LinkedIn URL."""
        query = """
        FOR p IN profiles
            FILTER p.linkedin == @linkedin
            LIMIT 1
            RETURN p
        """
        results = await self.execute_query(query, {"linkedin": linkedin})
        return Profile.from_dict(results[0]) if results else None

    async def find_by_extraction(self, extraction_key: str) -> Profile | None:
        """Find profile associated with an extraction via edge traversal."""
        query = """
        FOR p IN 1..1 INBOUND DOCUMENT(CONCAT("extractions/", @extraction_key)) profile_has_extraction
            LIMIT 1
            RETURN p
        """
        results = await self.execute_query(query, {"extraction_key": extraction_key})
        if results:
            return Profile.from_dict(results[0])

        query_fallback = """
        FOR p IN profiles
            FILTER @extraction_key IN p.source_extractions
            LIMIT 1
            RETURN p
        """
        results = await self.execute_query(query_fallback, {"extraction_key": extraction_key})
        return Profile.from_dict(results[0]) if results else None

    async def search(self, term: str, limit: int = 20) -> list[Profile]:
        """Search profiles by name or email."""
        query = """
        FOR p IN profiles
            FILTER CONTAINS(LOWER(p.full_name), LOWER(@term))
                OR CONTAINS(LOWER(p.email), LOWER(@term))
            LIMIT @limit
            RETURN p
        """
        results = await self.execute_query(query, {"term": term, "limit": limit})
        return [Profile.from_dict(doc) for doc in results]

    async def find_recent(self, limit: int = 50) -> list[Profile]:
        """Find recent profiles."""
        query = """
        FOR p IN profiles
            SORT p.created_at DESC
            LIMIT @limit
            RETURN p
        """
        results = await self.execute_query(query, {"limit": limit})
        return [Profile.from_dict(doc) for doc in results]

    async def list_with_stats(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        List profiles with extraction and substance counts.

        Returns summary info useful for frontend listing.
        """
        query = """
        FOR p IN profiles
            SORT p.created_at DESC
            LIMIT @limit
            LET extraction_count = LENGTH(
                FOR e IN 1..1 OUTBOUND p profile_has_extraction RETURN 1
            )
            LET substance_count = LENGTH(
                FOR s IN 1..1 OUTBOUND p profile_interested_in_substance RETURN 1
            )
            RETURN {
                key: p._key,
                full_name: p.full_name,
                credentials: p.credentials,
                email: p.email,
                linkedin: p.linkedin,
                created_at: p.created_at,
                updated_at: p.updated_at,
                extraction_count: extraction_count,
                substance_count: substance_count
            }
        """
        return await self.execute_query(query, {"limit": limit})

    async def ensure_edge_collections(self) -> None:
        """Ensure all profile edge collections exist."""
        collections = await self._db.collections()
        collection_names = [c["name"] for c in collections]

        for edge_coll in PROFILE_EDGE_COLLECTIONS:
            if edge_coll not in collection_names:
                await self._db.create_collection(edge_coll, col_type=CollectionType.EDGE)
                logger.debug("edge_collection_created", collection=edge_coll)

    async def create_extraction_edge(
        self,
        profile_key: str,
        extraction_key: str,
    ) -> bool:
        """Create edge from profile to extraction (profile_has_extraction)."""
        await self.ensure_edge_collections()

        edge_key = hashlib.md5(
            f"profiles/{profile_key}_extractions/{extraction_key}".encode()
        ).hexdigest()[:16]

        edge_doc = {
            "_key": edge_key,
            "_from": f"profiles/{profile_key}",
            "_to": f"extractions/{extraction_key}",
        }

        collection = self._db.collection("profile_has_extraction")

        exists = await collection.has(edge_key)
        if exists:
            logger.debug(
                "extraction_edge_exists",
                profile_key=profile_key,
                extraction_key=extraction_key,
            )
            return False

        try:
            await collection.insert(edge_doc)
            logger.debug(
                "extraction_edge_created",
                profile_key=profile_key,
                extraction_key=extraction_key,
            )
            return True
        except DocumentInsertError as e:
            if "unique constraint violated" in str(e):
                return False
            raise

    async def create_substance_edge(
        self,
        profile_key: str,
        substance_key: str,
    ) -> bool:
        """Create edge from profile to substance (profile_interested_in_substance)."""
        await self.ensure_edge_collections()

        edge_key = hashlib.md5(
            f"profiles/{profile_key}_substances/{substance_key}".encode()
        ).hexdigest()[:16]

        edge_doc = {
            "_key": edge_key,
            "_from": f"profiles/{profile_key}",
            "_to": f"substances/{substance_key}",
        }

        collection = self._db.collection("profile_interested_in_substance")

        exists = await collection.has(edge_key)
        if exists:
            logger.debug(
                "substance_edge_exists",
                profile_key=profile_key,
                substance_key=substance_key,
            )
            return False

        try:
            await collection.insert(edge_doc)
            logger.debug(
                "substance_edge_created",
                profile_key=profile_key,
                substance_key=substance_key,
            )
            return True
        except DocumentInsertError as e:
            if "unique constraint violated" in str(e):
                return False
            raise

    async def create_substance_edges_bulk(
        self,
        profile_key: str,
        substance_keys: list[str],
    ) -> int:
        """Create edges from profile to multiple substances."""
        count = 0
        for substance_key in substance_keys:
            if await self.create_substance_edge(profile_key, substance_key):
                count += 1
        return count

    async def get_profile_substances(self, profile_key: str) -> list[dict[str, Any]]:
        """Get all substances a profile is interested in via graph traversal."""
        query = """
        FOR s IN 1..1 OUTBOUND DOCUMENT(CONCAT("profiles/", @profile_key)) profile_interested_in_substance
            RETURN {
                key: s._key,
                name: s.name,
                unii: s.unii,
                formula: s.formula
            }
        """
        return await self.execute_query(query, {"profile_key": profile_key})

    async def get_profile_extractions(self, profile_key: str) -> list[dict[str, Any]]:
        """Get all extractions associated with a profile via graph traversal."""
        query = """
        FOR e IN 1..1 OUTBOUND DOCUMENT(CONCAT("profiles/", @profile_key)) profile_has_extraction
            RETURN {
                key: e._key,
                filename: e.filename,
                created_at: e.created_at,
                entities_count: LENGTH(e.entities)
            }
        """
        return await self.execute_query(query, {"profile_key": profile_key})

    async def get_profile_with_details(self, profile_key: str) -> dict[str, Any] | None:
        """
        Get profile with related details via graph traversal.

        Returns:
        - profile: Basic profile information
        - extractions: Extraction summaries (meta info for frontend)
        - substances: Substances with drugs, routes, and pharm classes
        - stats: Summary counts
        """
        query = """
        LET profile = DOCUMENT(CONCAT("profiles/", @profile_key))

        LET extractions = (
            FOR e IN 1..1 OUTBOUND profile profile_has_extraction
                LET meta = e.meta || {}
                LET quality = e.quality || {}
                RETURN {
                    key: e._key,
                    filename: e.filename,
                    status: e.status,
                    created_at: e.created_at,
                    doc_type: meta.doc_type,
                    therapeutic_areas: meta.therapeutic_areas,
                    total_entities: meta.total_entities,
                    avg_confidence: quality.avg_confidence
                }
        )

        LET substances = (
            FOR s IN 1..1 OUTBOUND profile profile_interested_in_substance
                LET drug_docs = (
                    FOR d IN 1..1 INBOUND s drug_has_substance
                        RETURN d
                )
                LET drugs = (
                    FOR d IN drug_docs
                        RETURN {
                            key: d._key,
                            brand_names: d.brand_names,
                            generic_names: d.generic_names,
                            sponsor_name: d.sponsor_name,
                            application_number: d.application_number
                        }
                )
                LET routes = UNIQUE(
                    FOR d IN drug_docs
                        FOR r IN 1..1 OUTBOUND d drug_has_route
                            RETURN { key: r._key, name: r.name }
                )
                LET dosage_forms = UNIQUE(
                    FOR d IN drug_docs
                        FOR df IN 1..1 OUTBOUND d drug_has_form
                            RETURN { key: df._key, name: df.name }
                )
                LET pharm_classes = UNIQUE(
                    FOR d IN drug_docs
                        FOR pc IN 1..1 OUTBOUND d drug_in_class
                            RETURN { key: pc._key, name: pc.name, class_type: pc.class_type }
                )
                LET manufacturers = UNIQUE(
                    FOR d IN drug_docs
                        FOR m IN 1..1 OUTBOUND d drug_by_manufacturer
                            RETURN { key: m._key, name: m.name }
                )
                RETURN {
                    key: s._key,
                    name: s.name,
                    unii: s.unii,
                    rxcui: s.rxcui,
                    is_enriched: s.is_enriched,
                    drugs: drugs,
                    routes: routes,
                    dosage_forms: dosage_forms,
                    pharm_classes: pharm_classes,
                    manufacturers: manufacturers,
                    drug_count: LENGTH(drugs)
                }
        )

        RETURN profile ? {
            profile: {
                key: profile._key,
                full_name: profile.full_name,
                credentials: profile.credentials,
                email: profile.email,
                phone: profile.phone,
                linkedin: profile.linkedin,
                location: profile.location,
                created_at: profile.created_at,
                updated_at: profile.updated_at
            },
            extractions: extractions,
            substances: substances,
            stats: {
                total_extractions: LENGTH(extractions),
                total_substances: LENGTH(substances)
            }
        } : null
        """
        results = await self.execute_query(query, {"profile_key": profile_key})
        return results[0] if results and results[0] else None
