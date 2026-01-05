"""
Extract endpoints - NER extraction from PDF + FDA enrichment.

POST /extract - Upload PDF file for entity extraction and enrichment
GET /extractions - List recent extractions with profile info
GET /extract/{extraction_id} - Get extraction by ID
"""

from fastapi import APIRouter, File, Query, UploadFile

from src.api.decorators import error_message
from src.api.dependencies import ContainerDep
from src.api.schemas.base import BaseResponse
from src.api.schemas.extract.response import (
    EntityNELResponse,
    ExtractAndEnrichDataResponse,
    ExtractAndEnrichResponse,
    ProfileResponse,
)
from src.api.schemas.extraction.response import (
    ExtractionListDataResponse,
    ExtractionListItem,
    ExtractionListResponse,
    ExtractionProfileSummary,
)
from src.infrastructure.pdf.extractor import PDFExtractor

router = APIRouter(tags=["Extraction"])


@router.post(
    "/extract",
    response_model=ExtractAndEnrichResponse,
    summary="Extract entities from PDF and enrich with FDA data",
    description="""
    Extract pharmaceutical entities from a PDF document, then enrich each drug
    with data from FDA, RxNorm, and UNII APIs.

    **Flow**:
    1. Extract text from PDF using PyMuPDF
    2. Use LLM (OpenAI) to identify drug entities (NER/NEL)
    3. Extract personal info (profile) if present
    4. For each BRAND/GENERIC drug found, fetch data from FDA/RxNorm/UNII
    5. Persist enriched data to the knowledge graph
    6. Create edges: profile -> extraction, profile -> substances

    **Response**: Simplified list of entities with NEL links and substance IDs.
    """,
    responses={
        400: {"model": BaseResponse, "description": "Invalid PDF or request"},
        500: {"model": BaseResponse, "description": "Extraction or enrichment failed"},
    },
)
@error_message("An error occurred while processing your document. Please try again.")
async def extract_entities(
    container: ContainerDep,
    file: UploadFile = File(..., description="PDF file to process"),
) -> ExtractAndEnrichResponse:
    """Extract entities from PDF and enrich with FDA data."""
    content = await file.read()
    filename = file.filename or "document.pdf"

    pdf_text = PDFExtractor().extract_from_bytes(content, filename).full_text

    ner_service = await container.get_ner_service()
    substance_service = await container.get_substance_service()

    result = await ner_service.extract_and_enrich(pdf_text, substance_service, filename)

    substance_map = {s.name.lower(): s for s in result.substances}

    entities_response: list[EntityNELResponse] = []
    for e in result.extraction_result.entities:
        substance_ref = substance_map.get(e.name.lower())

        entities_response.append(EntityNELResponse(
            name=e.name,
            type=e.type.value,
            linked_to=e.nel.linked_to if e.nel else None,
            relationship=e.nel.relationship.value if e.nel else None,
            substance_id=substance_ref.substance_id if substance_ref else None,
            url=substance_ref.url if substance_ref else None,
        ))

    profile_response: ProfileResponse | None = None
    if result.profile:
        profile_response = ProfileResponse(
            id=result.profile.key,
            full_name=result.profile.full_name,
            credentials=result.profile.credentials,
        )

    return ExtractAndEnrichResponse.ok(
        ExtractAndEnrichDataResponse(
            extraction_id=result.extraction_id,
            profile=profile_response,
            entities=entities_response,
        )
    )


@router.get(
    "/extractions",
    response_model=ExtractionListResponse,
    summary="List recent extractions",
    description="""
    Retrieve the most recent extractions with associated profile information.

    Returns extraction metadata including:
    - File information (hash, filename)
    - Extraction quality metrics (entity count, confidence)
    - Document metadata (type, therapeutic areas, drug density)
    - Linked profile summary (name, credentials, email)

    Results are sorted by creation date (newest first).
    """,
    responses={
        500: {"model": BaseResponse, "description": "Internal server error"},
    },
)
@error_message("An error occurred while fetching extractions. Please try again.")
async def list_extractions(
    container: ContainerDep,
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of extractions to return"),
) -> ExtractionListResponse:
    """List recent extractions with profile information."""
    extraction_service = await container.get_extraction_service()
    extractions = await extraction_service.list_recent(limit)

    items: list[ExtractionListItem] = []
    for e in extractions:
        profile_summary = None
        if e.profile_key:
            profile_summary = ExtractionProfileSummary(
                key=e.profile_key,
                full_name=e.profile_name,
                credentials=e.profile_credentials,
                email=e.profile_email,
            )

        items.append(
            ExtractionListItem(
                key=e.key,
                file_hash=e.file_hash,
                filename=e.filename,
                status=e.status,
                created_at=e.created_at,
                doc_type=e.doc_type,
                therapeutic_areas=e.therapeutic_areas,
                drug_density=e.drug_density,
                total_entities=e.total_entities,
                avg_confidence=e.avg_confidence,
                profile=profile_summary,
            )
        )

    return ExtractionListResponse(
        success=True,
        data=ExtractionListDataResponse(
            extractions=items,
            count=len(items),
        )
    )


@router.get(
    "/extract/{extraction_id}",
    response_model=ExtractAndEnrichResponse,
    summary="Get extraction by ID",
    description="""
    Retrieve a specific extraction by its ID (file_hash).

    Returns the same format as POST /extract, including:
    - Extraction ID
    - Profile information (if available)
    - List of extracted entities with NEL links and substance references
    """,
    responses={
        404: {"model": BaseResponse, "description": "Extraction not found"},
        500: {"model": BaseResponse, "description": "Internal server error"},
    },
)
@error_message("An error occurred while fetching the extraction. Please try again.")
async def get_extraction_by_id(
    container: ContainerDep,
    extraction_id: str,
) -> ExtractAndEnrichResponse:
    """Get extraction by ID with profile and entity information."""
    extraction_service = await container.get_extraction_service()
    result = await extraction_service.get_by_id(extraction_id)

    substance_map = {s.name.lower(): s for s in result.substances}

    entities_response: list[EntityNELResponse] = []
    for e in result.extraction_result.entities:
        substance_ref = substance_map.get(e.name.lower())

        entities_response.append(EntityNELResponse(
            name=e.name,
            type=e.type.value,
            linked_to=e.nel.linked_to if e.nel else None,
            relationship=e.nel.relationship.value if e.nel else None,
            substance_id=substance_ref.substance_id if substance_ref else None,
            url=substance_ref.url if substance_ref else None,
        ))

    profile_response: ProfileResponse | None = None
    if result.profile:
        profile_response = ProfileResponse(
            id=result.profile.key,
            full_name=result.profile.full_name,
            credentials=result.profile.credentials,
        )

    return ExtractAndEnrichResponse.ok(
        ExtractAndEnrichDataResponse(
            extraction_id=result.extraction_id,
            profile=profile_response,
            entities=entities_response,
        )
    )
