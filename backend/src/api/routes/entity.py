"""
Entity endpoint - Substance entity details.

GET /entity/{id} - Get substance details with all related data
"""

from fastapi import APIRouter, Path

from src.api.dependencies import ContainerDep
from src.api.schemas.base import BaseResponse
from src.api.schemas.entity.response import (
    DosageFormInfo,
    DrugInfo,
    DrugLabelInfo,
    EntitySearchResponse,
    EntitySearchResult,
    FDAApplicationInfo,
    InteractionInfo,
    ManufacturerInfo,
    PharmClassInfo,
    ProductInfo,
    ReactionInfo,
    RouteInfo,
    SubstanceProfileData,
    SubstanceProfileResponse,
)
from src.shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Entity"])


@router.get(
    "/entity/{substance_id}",
    response_model=SubstanceProfileResponse,
    summary="Get substance details",
    description="""
    Get detailed information about a pharmaceutical substance.

    Returns the COMPLETE substance profile from the knowledge graph, including:
    - Chemical identifiers (UNII, CAS, SMILES, InChI, PubChem)
    - Molecular properties (formula, weight, stereochemistry)
    - Commercial drugs containing this substance
    - Pharmacological classes (EPC, MOA, PE, CS)
    - Drug labels/package inserts (complete text)
    - FDA applications (NDA, ANDA, BLA)
    - NDC products and packages
    - Manufacturers
    - Administration routes
    - Dosage forms
    - Drug-drug interactions
    - Adverse reactions
    """,
    responses={
        404: {"model": BaseResponse, "description": "Substance not found"},
    },
)
async def get_substance_details(
    container: ContainerDep,
    substance_id: str = Path(..., description="Substance ID (e.g., 'ibuprofen', 'aspirin')"),
) -> SubstanceProfileResponse:
    """
    Substance Details Endpoint.

    GET /entity/{substance_id}

    Returns substance with ALL related data from the graph.
    """
    substance_service = await container.get_substance_service()
    profile_data = await substance_service.get_profile(substance_id)

    substance = profile_data["substance"]
    relations = profile_data["relations"]

    profile = SubstanceProfileData(
        key=substance.key,
        name=substance.name,
        unii=substance.unii,
        rxcui=substance.rxcui,
        cas_number=substance.cas_number,
        formula=substance.formula,
        molecular_weight=substance.molecular_weight,
        smiles=substance.smiles,
        inchi=substance.inchi,
        inchi_key=substance.inchi_key,
        pubchem_id=substance.pubchem_id,
        substance_class=substance.substance_class,
        stereochemistry=substance.stereochemistry,
        is_enriched=substance.is_enriched,
        enriched_at=substance.enriched_at,
        drugs=[
            DrugInfo(
                key=d["key"],
                application_number=d.get("application_number"),
                brand_names=d.get("brand_names", []),
                generic_names=d.get("generic_names", []),
                ndc_codes=d.get("ndc_codes", []),
                rxcui=d.get("rxcui", []),
                spl_id=d.get("spl_id", []),
                sponsor_name=d.get("sponsor_name"),
                drug_type=d.get("drug_type"),
                source=d.get("source", "api"),
                is_enriched=d.get("is_enriched", False),
            )
            for d in relations.get("drugs", [])
        ],
        pharm_classes=[
            PharmClassInfo(key=pc["key"], name=pc["name"], class_type=pc.get("class_type"))
            for pc in relations.get("pharm_classes", [])
        ],
        manufacturers=[
            ManufacturerInfo(key=m["key"], name=m["name"])
            for m in relations.get("manufacturers", [])
        ],
        routes=[
            RouteInfo(key=r["key"], name=r["name"])
            for r in relations.get("routes", [])
        ],
        dosage_forms=[
            DosageFormInfo(key=df["key"], name=df["name"])
            for df in relations.get("dosage_forms", [])
        ],
        products=[
            ProductInfo(
                key=p["key"],
                product_number=p.get("product_number"),
                package_ndc=p.get("package_ndc"),
                brand_name=p.get("brand_name"),
                dosage_form=p.get("dosage_form"),
                route=p.get("route"),
                marketing_status=p.get("marketing_status"),
                description=p.get("description"),
            )
            for p in relations.get("products", [])
        ],
        applications=[
            FDAApplicationInfo(
                key=app["key"],
                application_number=app["application_number"],
                submission_type=app.get("submission_type"),
                submission_number=app.get("submission_number"),
                submission_status=app.get("submission_status"),
                submission_status_date=app.get("submission_status_date"),
                review_priority=app.get("review_priority"),
            )
            for app in relations.get("applications", [])
        ],
        labels=[
            DrugLabelInfo(
                key=lbl["key"],
                spl_id=lbl.get("spl_id"),
                set_id=lbl.get("set_id"),
                version=lbl.get("version"),
                effective_time=lbl.get("effective_time"),
                description=lbl.get("description"),
                clinical_pharmacology=lbl.get("clinical_pharmacology"),
                mechanism_of_action=lbl.get("mechanism_of_action"),
                indications_and_usage=lbl.get("indications_and_usage"),
                dosage_and_administration=lbl.get("dosage_and_administration"),
                contraindications=lbl.get("contraindications"),
                warnings_and_cautions=lbl.get("warnings_and_cautions"),
                boxed_warning=lbl.get("boxed_warning"),
                adverse_reactions=lbl.get("adverse_reactions"),
                drug_interactions=lbl.get("drug_interactions"),
            )
            for lbl in relations.get("labels", [])
        ],
        interactions=[
            InteractionInfo(
                key=inter["key"],
                severity=inter.get("severity"),
                description=inter.get("description"),
                source_drug_rxcui=inter.get("source_drug_rxcui"),
                source_drug_name=inter.get("source_drug_name"),
                target_drug_rxcui=inter.get("target_drug_rxcui"),
                target_drug_name=inter.get("target_drug_name"),
            )
            for inter in relations.get("interactions", [])
        ],
        reactions=[
            ReactionInfo(
                key=rxn["key"],
                name=rxn["name"],
                meddra_version=rxn.get("meddra_version"),
            )
            for rxn in relations.get("reactions", [])
        ],
    )

    return SubstanceProfileResponse.ok(profile)


@router.get(
    "/entity",
    response_model=EntitySearchResponse,
    summary="Search entities",
    description="Search for pharmaceutical entities by name.",
    responses={
        400: {"model": BaseResponse, "description": "Invalid search query"},
    },
)
async def search_entities(
    container: ContainerDep,
    q: str,
    limit: int = 20,
) -> EntitySearchResponse:
    """Search entities by name."""
    logger.info("entity_search", query=q, limit=limit)

    drug_repo = await container.get_drug_repository()
    drugs = await drug_repo.search(q, limit=limit)

    results = [
        EntitySearchResult(
            key=d.key,
            name=d.brand_names[0] if d.brand_names else (d.generic_names[0] if d.generic_names else d.key),
            type=d.drug_type or "unknown",
        )
        for d in drugs
    ]

    return EntitySearchResponse.ok(results)
