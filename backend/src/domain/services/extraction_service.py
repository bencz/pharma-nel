"""
Extraction Service.

Business logic for extraction operations.
"""

from dataclasses import dataclass

from src.domain.entities.extraction import EntityType, ExtractionResult
from src.domain.entities.profile import Profile
from src.domain.exceptions.extraction import ExtractionNotFoundError
from src.infrastructure.database.repositories.extraction_repository import ExtractionRepository
from src.infrastructure.database.repositories.profile_repository import ProfileRepository
from src.infrastructure.database.repositories.substance_repository import SubstanceRepository
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class ExtractedSubstanceRef:
    """Reference to an extracted substance."""

    name: str
    substance_id: str
    url: str


@dataclass(slots=True)
class ExtractionDetail:
    """Complete extraction with profile and substance references."""

    extraction_id: str
    extraction_result: ExtractionResult
    profile: Profile | None
    substances: list[ExtractedSubstanceRef]


@dataclass(slots=True)
class ExtractionWithProfile:
    """Extraction data with associated profile information."""

    key: str
    file_hash: str | None
    filename: str | None
    status: str | None
    created_at: str | None
    doc_type: str | None
    therapeutic_areas: list[str]
    drug_density: str | None
    total_entities: int
    avg_confidence: int
    profile_key: str | None
    profile_name: str | None
    profile_credentials: list[str]
    profile_email: str | None


class ExtractionService:
    """Service for extraction-related operations."""

    def __init__(
        self,
        extraction_repository: ExtractionRepository,
        profile_repository: ProfileRepository | None = None,
        substance_repository: SubstanceRepository | None = None,
    ) -> None:
        self._repository = extraction_repository
        self._profile_repo = profile_repository
        self._substance_repo = substance_repository

    async def get_by_id(self, extraction_id: str) -> ExtractionDetail:
        """
        Get extraction by ID with profile and substance references.

        Args:
            extraction_id: The extraction ID (file_hash or _key)

        Returns:
            ExtractionDetail with extraction, profile, and substances
        """
        cached = await self._repository.find_by_key(extraction_id)
        if not cached:
            cached = await self._repository.find_by_file_hash(extraction_id)

        if not cached:
            raise ExtractionNotFoundError(extraction_id)

        extraction_result = ExtractionResult.from_cached(cached)

        profile: Profile | None = None
        if self._profile_repo:
            profile = await self._profile_repo.find_by_extraction(extraction_id)

        substance_names = list({
            e.name for e in extraction_result.entities
            if e.type in (EntityType.BRAND, EntityType.GENERIC)
        })

        refs: list[ExtractedSubstanceRef] = []
        if substance_names and self._substance_repo:
            for name in substance_names:
                substance = await self._substance_repo.find_by_name(name)
                if substance:
                    refs.append(ExtractedSubstanceRef(
                        name=name,
                        substance_id=substance.key,
                        url=f"entity/{substance.key}",
                    ))

        return ExtractionDetail(
            extraction_id=extraction_id,
            extraction_result=extraction_result,
            profile=profile,
            substances=refs,
        )

    async def list_recent(self, limit: int = 100) -> list[ExtractionWithProfile]:
        """List recent extractions with profile information."""
        raw_results = await self._repository.find_recent_with_profile(limit)

        extractions: list[ExtractionWithProfile] = []
        for doc in raw_results:
            meta = doc.get("meta") or {}
            quality = doc.get("quality") or {}
            profile = doc.get("profile")

            extractions.append(
                ExtractionWithProfile(
                    key=doc.get("_key", ""),
                    file_hash=doc.get("file_hash"),
                    filename=doc.get("filename"),
                    status=doc.get("status"),
                    created_at=doc.get("created_at"),
                    doc_type=meta.get("doc_type"),
                    therapeutic_areas=meta.get("therapeutic_areas", []),
                    drug_density=meta.get("drug_density"),
                    total_entities=meta.get("total_entities", 0),
                    avg_confidence=quality.get("avg_confidence", 0),
                    profile_key=profile.get("_key") if profile else None,
                    profile_name=profile.get("full_name") if profile else None,
                    profile_credentials=profile.get("credentials", []) if profile else [],
                    profile_email=profile.get("email") if profile else None,
                )
            )

        logger.debug("extractions_listed", count=len(extractions))
        return extractions
