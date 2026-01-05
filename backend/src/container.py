"""
Dependency Injection Container.

Provides singleton instances of services, repositories, and clients.
Easy to mock for testing.
"""

import httpx

from src.domain.services.drug_service import DrugService
from src.domain.services.extraction_service import ExtractionService
from src.domain.services.ner_service import NERService
from src.domain.services.profile_service import ProfileService
from src.domain.services.substance_enrichment_service import SubstanceEnrichmentService
from src.domain.services.substance_service import SubstanceService
from src.infrastructure.clients.fda_client import FDAClient, FDAClientConfig
from src.infrastructure.clients.openai_client import OpenAIClient, OpenAIClientConfig
from src.infrastructure.clients.rxnorm_client import RxNormClient, RxNormClientConfig
from src.infrastructure.clients.unii_client import UNIIClient, UNIIClientConfig
from src.infrastructure.database.connection import ArangoConnection
from src.infrastructure.database.repositories.drug_repository import DrugRepository
from src.infrastructure.database.repositories.extraction_repository import ExtractionRepository
from src.infrastructure.database.repositories.openfda_graph_repository import OpenFDAGraphRepository
from src.infrastructure.database.repositories.profile_repository import ProfileRepository
from src.infrastructure.database.repositories.substance_repository import SubstanceRepository
from src.shared.config import Settings
from src.shared.logging import get_logger

logger = get_logger(__name__)


class Container:
    """
    Dependency Injection Container.

    Provides lazy-loaded singleton instances of all application dependencies.
    """

    _instance: "Container | None" = None

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

        self._arango_connection: ArangoConnection | None = None
        self._http_client: httpx.AsyncClient | None = None

        self._fda_client: FDAClient | None = None
        self._rxnorm_client: RxNormClient | None = None
        self._unii_client: UNIIClient | None = None
        self._openai_client: OpenAIClient | None = None

        self._drug_repository: DrugRepository | None = None
        self._extraction_repository: ExtractionRepository | None = None
        self._profile_repository: ProfileRepository | None = None
        self._substance_repository: SubstanceRepository | None = None
        self._openfda_graph_repository: OpenFDAGraphRepository | None = None
        self._substance_enrichment_service: SubstanceEnrichmentService | None = None
        self._drug_service: DrugService | None = None
        self._substance_service: SubstanceService | None = None
        self._ner_service: NERService | None = None
        self._extraction_service: ExtractionService | None = None
        self._profile_service: ProfileService | None = None

    @classmethod
    def get_instance(cls) -> "Container":
        if cls._instance is None:
            raise RuntimeError("Container not initialized. Call Container.initialize() first.")
        return cls._instance

    @classmethod
    def initialize(cls, settings: Settings) -> "Container":
        if cls._instance is not None:
            logger.warning("container_already_initialized")
            return cls._instance

        cls._instance = cls(settings)
        logger.info("container_initialized")
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def fda_client(self) -> FDAClient:
        if self._fda_client is None:
            self._fda_client = FDAClient(
                FDAClientConfig(
                    base_url=self._settings.fda_base_url,
                    api_key=self._settings.fda_api_key,
                    timeout=self._settings.fda_timeout,
                    max_retries=self._settings.fda_max_retries,
                    verify_ssl=self._settings.http_verify_ssl,
                )
            )
        return self._fda_client

    @property
    def rxnorm_client(self) -> RxNormClient:
        if self._rxnorm_client is None:
            self._rxnorm_client = RxNormClient(
                RxNormClientConfig(
                    base_url=self._settings.rxnorm_base_url,
                    timeout=self._settings.rxnorm_timeout,
                    max_retries=self._settings.rxnorm_max_retries,
                    verify_ssl=self._settings.http_verify_ssl,
                )
            )
        return self._rxnorm_client

    @property
    def unii_client(self) -> UNIIClient:
        if self._unii_client is None:
            self._unii_client = UNIIClient(
                UNIIClientConfig(
                    base_url=self._settings.unii_base_url,
                    timeout=self._settings.unii_timeout,
                    max_retries=self._settings.unii_max_retries,
                    verify_ssl=self._settings.http_verify_ssl,
                )
            )
        return self._unii_client

    @property
    def openai_client(self) -> OpenAIClient:
        if self._openai_client is None:
            if not self._settings.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY not configured")
            self._openai_client = OpenAIClient(
                OpenAIClientConfig(
                    api_key=self._settings.openai_api_key,
                    model=self._settings.openai_model,
                    max_tokens=16000,
                    temperature=0.1,
                )
            )
        return self._openai_client

    @property
    def arango_connection(self) -> ArangoConnection:
        if self._arango_connection is None:
            self._arango_connection = ArangoConnection(self._settings)
        return self._arango_connection

    async def get_drug_repository(self) -> DrugRepository:
        """Get drug repository (async - needs db connection)."""
        if self._drug_repository is None:
            db = await self.arango_connection.get_db()
            self._drug_repository = DrugRepository(db)
        return self._drug_repository

    async def get_extraction_repository(self) -> ExtractionRepository:
        """Get extraction repository (async - needs db connection)."""
        if self._extraction_repository is None:
            db = await self.arango_connection.get_db()
            self._extraction_repository = ExtractionRepository(db)
        return self._extraction_repository

    async def get_substance_repository(self) -> SubstanceRepository:
        """Get substance repository (async - needs db connection)."""
        if self._substance_repository is None:
            db = await self.arango_connection.get_db()
            self._substance_repository = SubstanceRepository(db)
        return self._substance_repository

    async def get_profile_repository(self) -> ProfileRepository:
        """Get profile repository (async - needs db connection)."""
        if self._profile_repository is None:
            db = await self.arango_connection.get_db()
            self._profile_repository = ProfileRepository(db)
        return self._profile_repository

    async def get_openfda_graph_repository(self) -> OpenFDAGraphRepository:
        """Get OpenFDA graph repository (async - needs db connection)."""
        if self._openfda_graph_repository is None:
            db = await self.arango_connection.get_db()
            self._openfda_graph_repository = OpenFDAGraphRepository(db)
        return self._openfda_graph_repository

    @property
    def substance_enrichment_service(self) -> SubstanceEnrichmentService:
        """Get substance enrichment service (uses FDA, RxNorm, UNII clients)."""
        if self._substance_enrichment_service is None:
            self._substance_enrichment_service = SubstanceEnrichmentService(
                fda_client=self.fda_client,
                rxnorm_client=self.rxnorm_client,
                unii_client=self.unii_client,
            )
        return self._substance_enrichment_service

    async def get_drug_service(self) -> DrugService:
        """Get drug service (async - needs repositories)."""
        if self._drug_service is None:
            drug_repo = await self.get_drug_repository()
            graph_repo = await self.get_openfda_graph_repository()
            self._drug_service = DrugService(
                drug_repository=drug_repo,
                graph_repository=graph_repo,
            )
        return self._drug_service

    async def get_substance_service(self) -> SubstanceService:
        """Get substance service (async - needs repositories)."""
        if self._substance_service is None:
            substance_repo = await self.get_substance_repository()
            graph_repo = await self.get_openfda_graph_repository()
            self._substance_service = SubstanceService(
                substance_repository=substance_repo,
                graph_repository=graph_repo,
                enrichment_service=self.substance_enrichment_service,
            )
        return self._substance_service

    async def get_ner_service(self) -> NERService:
        """Get NER service (async - needs extraction and profile repositories)."""
        if self._ner_service is None:
            extraction_repo = await self.get_extraction_repository()
            profile_repo = await self.get_profile_repository()
            self._ner_service = NERService(
                self.openai_client,
                extraction_repo,
                profile_repo,
            )
        return self._ner_service

    async def get_extraction_service(self) -> ExtractionService:
        """Get extraction service (async - needs repositories)."""
        if self._extraction_service is None:
            extraction_repo = await self.get_extraction_repository()
            profile_repo = await self.get_profile_repository()
            substance_repo = await self.get_substance_repository()
            self._extraction_service = ExtractionService(
                extraction_repository=extraction_repo,
                profile_repository=profile_repo,
                substance_repository=substance_repo,
            )
        return self._extraction_service

    async def get_profile_service(self) -> ProfileService:
        """Get profile service (async - needs profile repository)."""
        if self._profile_service is None:
            profile_repo = await self.get_profile_repository()
            self._profile_service = ProfileService(profile_repo)
        return self._profile_service

    async def close(self) -> None:
        """Close all client connections."""
        if self._arango_connection:
            await self._arango_connection.close()
            self._arango_connection = None

        if self._fda_client:
            await self._fda_client.close()
            self._fda_client = None

        if self._rxnorm_client:
            await self._rxnorm_client.close()
            self._rxnorm_client = None

        if self._unii_client:
            await self._unii_client.close()
            self._unii_client = None

        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        logger.info("container_closed")


def get_container() -> Container:
    """FastAPI dependency to get the container instance."""
    return Container.get_instance()
