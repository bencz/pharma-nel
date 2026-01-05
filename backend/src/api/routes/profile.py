"""
Profile endpoints.

GET /profiles - List profiles with summary stats
GET /profile/{profile_id} - Get profile with details
"""

from fastapi import APIRouter, Query

from src.api.decorators import error_message
from src.api.dependencies import ContainerDep
from src.api.schemas.base import BaseResponse
from src.api.schemas.profile.response import (
    ProfileDetailData,
    ProfileDetailResponse,
    ProfileExtraction,
    ProfileInfo,
    ProfileListData,
    ProfileListItem,
    ProfileListResponse,
    ProfileLocation,
    ProfileStats,
    ProfileSubstance,
    SubstanceDosageForm,
    SubstanceDrug,
    SubstanceManufacturer,
    SubstancePharmClass,
    SubstanceRoute,
)

router = APIRouter(tags=["Profile"])


@router.get(
    "/profile/{profile_id}",
    response_model=ProfileDetailResponse,
    summary="Get profile with details",
    description="""
    Retrieve a profile with related information via graph traversal.

    Returns:
    - **profile**: Basic profile information (name, credentials, contact)
    - **extractions**: Extraction summaries (use GET /extract/{key} for full details)
    - **substances**: Substances of interest (use GET /entity/{key} for full details)
    - **stats**: Summary statistics
    """,
    responses={
        404: {"model": BaseResponse, "description": "Profile not found"},
        500: {"model": BaseResponse, "description": "Internal server error"},
    },
)
@error_message("An error occurred while fetching the profile. Please try again.")
async def get_profile_details(
    container: ContainerDep,
    profile_id: str,
) -> ProfileDetailResponse:
    """Get profile with related details."""
    profile_service = await container.get_profile_service()
    result = await profile_service.get_profile_details(profile_id)

    profile_data = result.get("profile", {})
    location_data = profile_data.get("location")

    location = None
    if location_data:
        location = ProfileLocation(
            city=location_data.get("city"),
            state=location_data.get("state"),
            country=location_data.get("country"),
        )

    profile_info = ProfileInfo(
        key=profile_data.get("key", ""),
        full_name=profile_data.get("full_name"),
        credentials=profile_data.get("credentials", []),
        email=profile_data.get("email"),
        phone=profile_data.get("phone"),
        linkedin=profile_data.get("linkedin"),
        location=location,
        created_at=profile_data.get("created_at"),
        updated_at=profile_data.get("updated_at"),
    )

    extractions = [
        ProfileExtraction(
            key=e.get("key", ""),
            filename=e.get("filename"),
            status=e.get("status"),
            created_at=e.get("created_at"),
            doc_type=e.get("doc_type"),
            therapeutic_areas=e.get("therapeutic_areas", []),
            total_entities=e.get("total_entities", 0),
            avg_confidence=e.get("avg_confidence", 0),
        )
        for e in result.get("extractions", [])
    ]

    substances = [
        ProfileSubstance(
            key=s.get("key", ""),
            name=s.get("name"),
            unii=s.get("unii"),
            rxcui=s.get("rxcui"),
            is_enriched=s.get("is_enriched", False),
            drugs=[
                SubstanceDrug(
                    key=d.get("key", ""),
                    brand_names=d.get("brand_names", []),
                    generic_names=d.get("generic_names", []),
                    sponsor_name=d.get("sponsor_name"),
                    application_number=d.get("application_number"),
                )
                for d in s.get("drugs", [])
            ],
            routes=[
                SubstanceRoute(
                    key=r.get("key", ""),
                    name=r.get("name"),
                )
                for r in s.get("routes", [])
            ],
            dosage_forms=[
                SubstanceDosageForm(
                    key=df.get("key", ""),
                    name=df.get("name"),
                )
                for df in s.get("dosage_forms", [])
            ],
            pharm_classes=[
                SubstancePharmClass(
                    key=pc.get("key", ""),
                    name=pc.get("name"),
                    class_type=pc.get("class_type"),
                )
                for pc in s.get("pharm_classes", [])
            ],
            manufacturers=[
                SubstanceManufacturer(
                    key=m.get("key", ""),
                    name=m.get("name"),
                )
                for m in s.get("manufacturers", [])
            ],
            drug_count=s.get("drug_count", 0),
        )
        for s in result.get("substances", [])
    ]

    stats_data = result.get("stats", {})
    stats = ProfileStats(
        total_extractions=stats_data.get("total_extractions", 0),
        total_substances=stats_data.get("total_substances", 0),
    )

    return ProfileDetailResponse(
        success=True,
        data=ProfileDetailData(
            profile=profile_info,
            extractions=extractions,
            substances=substances,
            stats=stats,
        ),
    )


@router.get(
    "/profiles",
    response_model=ProfileListResponse,
    summary="List profiles",
    description="""
    List profiles with summary statistics.

    Returns:
    - **profiles**: List of profile summaries with extraction/substance counts
    - **count**: Total number of profiles returned

    Results are sorted by creation date (newest first).
    """,
    responses={
        500: {"model": BaseResponse, "description": "Internal server error"},
    },
)
@error_message("An error occurred while fetching profiles. Please try again.")
async def list_profiles(
    container: ContainerDep,
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of profiles to return"),
) -> ProfileListResponse:
    """List profiles with summary stats."""
    profile_service = await container.get_profile_service()
    profiles = await profile_service.list_profiles(limit)

    items = [
        ProfileListItem(
            key=p.get("key", ""),
            full_name=p.get("full_name"),
            credentials=p.get("credentials", []),
            email=p.get("email"),
            linkedin=p.get("linkedin"),
            created_at=p.get("created_at"),
            updated_at=p.get("updated_at"),
            extraction_count=p.get("extraction_count", 0),
            substance_count=p.get("substance_count", 0),
        )
        for p in profiles
    ]

    return ProfileListResponse(
        success=True,
        data=ProfileListData(
            profiles=items,
            count=len(items),
        ),
    )
