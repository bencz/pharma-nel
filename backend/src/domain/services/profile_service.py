"""
Profile Service.

Business logic for profile operations.
"""

from src.domain.exceptions.profile import ProfileNotFoundError
from src.infrastructure.database.repositories.profile_repository import ProfileRepository
from src.shared.logging import get_logger

logger = get_logger(__name__)


class ProfileService:
    """Service for profile-related operations."""

    def __init__(self, profile_repository: ProfileRepository) -> None:
        self._repository = profile_repository

    async def get_profile_details(self, profile_id: str) -> dict:
        """
        Get complete profile with all related details.

        Args:
            profile_id: The profile key

        Returns:
            Dict with profile, extractions, substances, drugs, and stats
        """
        result = await self._repository.get_profile_with_details(profile_id)

        if not result:
            raise ProfileNotFoundError(profile_id)

        logger.debug(
            "profile_details_fetched",
            profile_id=profile_id,
            extractions=result.get("stats", {}).get("total_extractions", 0),
            substances=result.get("stats", {}).get("total_substances", 0),
        )

        return result

    async def list_profiles(self, limit: int = 100) -> list[dict]:
        """
        List profiles with summary stats.

        Args:
            limit: Maximum number of profiles to return

        Returns:
            List of profile summaries with extraction/substance counts
        """
        profiles = await self._repository.list_with_stats(limit)
        logger.debug("profiles_listed", count=len(profiles))
        return profiles
