"""
Base Repository with schema definition support (Async).

All repositories inherit from this base class.
Uses python-arango-async for async database operations.
"""

from dataclasses import dataclass
from typing import Any, ClassVar, Generic, TypeVar

from arangoasync.collection import Collection
from arangoasync.database import Database

from src.shared.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass(slots=True)
class IndexDefinition:
    """Definition for a collection index."""

    fields: list[str]
    type: str = "persistent"
    unique: bool = False
    sparse: bool = False
    name: str | None = None


@dataclass(slots=True)
class EdgeDefinition:
    """Definition for a graph edge collection."""

    collection: str
    from_collections: list[str]
    to_collections: list[str]


class BaseRepository(Generic[T]):
    """
    Base async repository for ArangoDB collections.

    Provides common CRUD operations and schema management.
    Each repository defines its own collection schema via class variables.
    """

    collection_name: ClassVar[str] = ""
    indices: ClassVar[list[IndexDefinition]] = []
    edge_definitions: ClassVar[list[EdgeDefinition]] = []

    def __init__(self, db: Database) -> None:
        self._db = db
        self._collection: Collection | None = None

    async def get_collection(self) -> Collection:
        """Get or create the collection."""
        if self._collection is None:
            collections = await self._db.collections()
            collection_names = [c["name"] for c in collections]

            if self.collection_name not in collection_names:
                self._collection = await self._db.create_collection(self.collection_name)
                logger.info("collection_created", collection=self.collection_name)
            else:
                self._collection = self._db.collection(self.collection_name)

        return self._collection

    async def ensure_indices(self) -> None:
        """Create indices defined for this repository."""
        collection = await self.get_collection()

        for idx in self.indices:
            try:
                await collection.add_index(
                    type=idx.type,
                    fields=idx.fields,
                    options={
                        "unique": idx.unique,
                        "sparse": idx.sparse,
                        "name": idx.name,
                    } if idx.name else {
                        "unique": idx.unique,
                        "sparse": idx.sparse,
                    },
                )
                logger.debug("index_created", collection=self.collection_name, fields=idx.fields)
            except Exception as e:
                logger.warning("index_creation_failed", collection=self.collection_name, error=str(e))

    async def insert(self, document: dict[str, Any]) -> dict[str, Any]:
        """Insert a document."""
        collection = await self.get_collection()
        result = await collection.insert(document, return_new=True)
        return result["new"]

    async def upsert(self, document: dict[str, Any], key_field: str = "_key") -> dict[str, Any]:
        """Insert or update a document."""
        collection = await self.get_collection()
        key = document.get(key_field)

        if key:
            exists = await collection.has(key)
            if exists:
                result = await collection.update(document, return_new=True)
                return result["new"]

        result = await collection.insert(document, return_new=True, overwrite=True)
        return result["new"]

    async def find_by_key(self, key: str) -> dict[str, Any] | None:
        """Find document by _key."""
        collection = await self.get_collection()
        exists = await collection.has(key)
        if exists:
            return await collection.get(key)
        return None

    async def find_all(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Find all documents with pagination."""
        query = f"""
        FOR doc IN {self.collection_name}
            LIMIT @offset, @limit
            RETURN doc
        """
        return await self.execute_query(query, {"offset": offset, "limit": limit})

    async def execute_query(
        self,
        query: str,
        bind_vars: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute an AQL query."""
        cursor = await self._db.aql.execute(query, bind_vars=bind_vars or {})
        results = []
        async with cursor:
            async for doc in cursor:
                results.append(doc)
        return results

    async def delete_by_key(self, key: str) -> bool:
        """Delete document by _key."""
        collection = await self.get_collection()
        exists = await collection.has(key)
        if exists:
            await collection.delete(key)
            return True
        return False

    async def count(self) -> int:
        """Count documents in collection."""
        collection = await self.get_collection()
        return await collection.count()
