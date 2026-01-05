"""
ArangoDB Async Connection Management.

Provides async connection pool and database access using python-arango-async.
"""

from typing import Any

from arangoasync import ArangoClient
from arangoasync.auth import Auth
from arangoasync.database import Database

from src.shared.config import Settings
from src.shared.logging import get_logger

logger = get_logger(__name__)


class ArangoConnection:
    """
    ArangoDB async connection manager.

    Provides async connection initialization and health checking.
    Uses context manager pattern for proper resource cleanup.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: ArangoClient | None = None
        self._db: Database | None = None
        self._auth: Auth | None = None

    @property
    def auth(self) -> Auth:
        if self._auth is None:
            self._auth = Auth(
                username=self._settings.arango_user,
                password=self._settings.arango_password,
            )
        return self._auth

    async def get_client(self) -> ArangoClient:
        """Get or create the ArangoDB client."""
        if self._client is None:
            self._client = ArangoClient(hosts=self._settings.arango_host)
            logger.info("arango_client_created", host=self._settings.arango_host)
        return self._client

    async def get_db(self) -> Database:
        """Get or create the database connection."""
        if self._db is None:
            client = await self.get_client()
            self._db = await client.db(self._settings.arango_database, auth=self.auth)
            logger.info(
                "arango_db_connected",
                database=self._settings.arango_database,
            )
        return self._db

    async def health_check(self) -> dict[str, Any]:
        """Check database connectivity and return status."""
        try:
            db = await self.get_db()
            version = await db.version()
            return {
                "healthy": True,
                "version": version,
            }
        except Exception as e:
            logger.error("arango_health_check_failed", error=str(e))
            return {
                "healthy": False,
                "error": str(e),
            }

    async def ensure_database(self) -> None:
        """Ensure the database exists, create if not."""
        client = await self.get_client()
        sys_db = await client.db("_system", auth=self.auth)

        databases = await sys_db.databases()
        if self._settings.arango_database not in databases:
            await sys_db.create_database(self._settings.arango_database)
            logger.info("arango_database_created", database=self._settings.arango_database)

    async def close(self) -> None:
        """Close the connection."""
        if self._client:
            await self._client.close()
            self._client = None
            self._db = None
            logger.info("arango_connection_closed")
