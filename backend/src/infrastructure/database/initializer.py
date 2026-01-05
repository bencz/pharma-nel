"""
Database Initializer.

Handles automatic initialization of database, collections, indices and graphs.
"""

import asyncio

from src.container import Container
from src.infrastructure.database.repositories.base import BaseRepository
from src.shared.logging import get_logger

logger = get_logger(__name__)


class DatabaseInitializer:
    """
    Initializes database schema on application startup.

    Automatically discovers and initializes all repositories from Container.
    """

    def __init__(self, container: "Container") -> None:
        self._container = container

    async def initialize(self) -> None:
        """Initialize database, all collections, indices and graphs."""
        logger.info("database_initialization_starting")

        await self._container.arango_connection.ensure_database()

        repositories = await self._get_all_repositories()

        init_tasks = [self._initialize_repository(repo) for repo in repositories]
        await asyncio.gather(*init_tasks)

        logger.info(
            "database_initialization_complete",
            repositories_initialized=len(repositories),
        )

    async def _get_all_repositories(self) -> list[BaseRepository]:
        """Get all repository instances from container."""
        return list(await asyncio.gather(
            self._container.get_drug_repository(),
            self._container.get_extraction_repository(),
            self._container.get_profile_repository(),
            self._container.get_substance_repository(),
            self._container.get_openfda_graph_repository(),
        ))

    async def _initialize_repository(self, repo: BaseRepository) -> None:
        """Initialize a single repository (collection + indices + graph if applicable)."""
        await repo.ensure_indices()

        if hasattr(repo, "ensure_graph"):
            await repo.ensure_graph()

        logger.debug(
            "repository_initialized",
            collection=repo.collection_name,
        )
