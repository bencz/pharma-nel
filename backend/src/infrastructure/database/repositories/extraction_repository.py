"""
Extraction Repository (Async).

Handles persistence of NER/NEL extraction results to ArangoDB.
"""

from typing import Any, ClassVar

from src.domain.entities.extraction import ExtractionResult
from src.infrastructure.database.repositories.base import (
    BaseRepository,
    IndexDefinition,
)
from src.shared.logging import get_logger

logger = get_logger(__name__)


class ExtractionRepository(BaseRepository[ExtractionResult]):
    """Async repository for NER/NEL extraction results."""

    collection_name: ClassVar[str] = "extractions"

    indices: ClassVar[list[IndexDefinition]] = [
        IndexDefinition(fields=["file_hash"], unique=True),
        IndexDefinition(fields=["filename"], type="persistent"),
        IndexDefinition(fields=["created_at"], type="persistent"),
        IndexDefinition(fields=["status"], type="persistent"),
    ]

    async def save_extraction(self, extraction_data: dict[str, Any]) -> dict[str, Any]:
        """Save extraction result. Handles legacy documents with different _key."""
        file_hash = extraction_data.get("file_hash")

        if file_hash:
            existing = await self.find_by_file_hash(file_hash)
            if existing and existing.get("_key") != extraction_data.get("_key"):
                await self.delete_by_key(existing["_key"])
                logger.debug("deleted_legacy_extraction", old_key=existing["_key"], file_hash=file_hash)

        return await self.upsert(extraction_data)

    async def find_by_key(self, key: str) -> dict[str, Any] | None:
        """Find extraction by _key (file hash)."""
        return await super().find_by_key(key)

    async def find_by_filename(self, filename: str) -> list[dict[str, Any]]:
        """Find extractions by filename."""
        query = """
        FOR e IN extractions
            FILTER e.filename == @filename
            SORT e.created_at DESC
            RETURN e
        """
        return await self.execute_query(query, {"filename": filename})

    async def find_by_file_hash(self, file_hash: str) -> dict[str, Any] | None:
        """Find extraction by file hash."""
        query = """
        FOR e IN extractions
            FILTER e.file_hash == @file_hash
            LIMIT 1
            RETURN e
        """
        results = await self.execute_query(query, {"file_hash": file_hash})
        return results[0] if results else None

    async def find_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """Find recent extractions."""
        query = """
        FOR e IN extractions
            SORT e.created_at DESC
            LIMIT @limit
            RETURN e
        """
        return await self.execute_query(query, {"limit": limit})

    async def find_recent_with_profile(self, limit: int = 100) -> list[dict[str, Any]]:
        """Find recent extractions with linked profile information via graph traversal."""
        query = """
        FOR e IN extractions
            SORT e.created_at DESC
            LIMIT @limit
            LET profile = FIRST(
                FOR v, edge IN 1..1 INBOUND e profile_has_extraction
                    RETURN v
            )
            RETURN {
                _key: e._key,
                file_hash: e.file_hash,
                filename: e.filename,
                status: e.status,
                created_at: e.created_at,
                meta: e.meta,
                quality: e.quality,
                profile: profile ? {
                    _key: profile._key,
                    full_name: profile.full_name,
                    credentials: profile.credentials,
                    email: profile.email
                } : null
            }
        """
        return await self.execute_query(query, {"limit": limit})
