"""
Named Entity Recognition Service.

Extracts pharmaceutical entities from text using LLM and persists to ArangoDB.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.domain.entities.extraction import EntityType, ExtractionResult
from src.domain.entities.profile import Profile, generate_profile_key
from src.domain.exceptions.extraction import ExtractionFailedError
from src.domain.ports.clients import ILLMClient, LLMMessage
from src.domain.services.substance_service import SubstanceService
from src.infrastructure.database.repositories.extraction_repository import ExtractionRepository
from src.infrastructure.database.repositories.profile_repository import ProfileRepository
from src.prompts import get_ner_system_prompt, get_ner_user_prompt
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class ExtractedSubstanceReference:
    """Reference to an extracted and enriched substance."""

    name: str
    substance_id: str
    url: str


@dataclass(slots=True)
class ExtractAndEnrichResult:
    """Complete result from extract_and_enrich operation."""

    extraction_id: str
    extraction_result: ExtractionResult
    profile: Profile | None
    substances: list[ExtractedSubstanceReference]


def compute_file_hash(content: bytes) -> str:
    """Compute SHA256 hash of file content for use as document key."""
    return hashlib.sha256(content).hexdigest()[:32]


class NERService:
    """
    Named Entity Recognition service for pharmaceutical entities.

    Uses LLM to extract drug names, generic names, development codes,
    and active ingredients from text documents.
    Persists extraction results to ArangoDB.
    """

    def __init__(
        self,
        llm_client: ILLMClient,
        extraction_repository: ExtractionRepository | None = None,
        profile_repository: ProfileRepository | None = None,
    ) -> None:
        self._llm = llm_client
        self._extraction_repo = extraction_repository
        self._profile_repo = profile_repository

    async def extract_from_text(
        self,
        text: str,
        filename: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 8000,
    ) -> ExtractionResult:
        """
        Extract pharmaceutical entities from text.

        Args:
            text: Document text to extract entities from
            filename: Optional filename for reference
            temperature: LLM temperature (lower = more deterministic)
            max_tokens: Maximum tokens for LLM response

        Returns:
            ExtractionResult with extracted entities
        """
        text_bytes = text.encode("utf-8")
        file_hash = compute_file_hash(text_bytes)

        cached = await self._get_cached_extraction(file_hash)
        if cached:
            return cached

        logger.info("ner_extraction_started", text_length=len(text), file_hash=file_hash)

        messages = [
            LLMMessage(role="system", content=get_ner_system_prompt()),
            LLMMessage(role="user", content=get_ner_user_prompt(text)),
        ]

        response = await self._llm.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        parsed = self._parse_response(response.content)

        result = ExtractionResult.from_llm_response(
            data=parsed,
            model=response.model,
            tokens=response.usage.get("total_tokens", 0),
        )

        if self._extraction_repo:
            await self._persist_extraction(
                file_hash=file_hash,
                filename=filename,
                extracted_text=text,
                llm_response=response.content,
                result=result,
                source_type="text",
            )

        logger.info(
            "ner_extraction_completed",
            file_hash=file_hash,
            entities_count=len(result.entities),
            tokens_used=result.tokens_used,
        )

        return result

    async def _persist_extraction(
        self,
        file_hash: str,
        filename: str | None,
        extracted_text: str | None,
        llm_response: str,
        result: ExtractionResult,
        source_type: str,
    ) -> None:
        """Persist extraction result to ArangoDB."""
        now = datetime.now(UTC).isoformat()

        extraction_doc = {
            "_key": file_hash,
            "file_hash": file_hash,
            "filename": filename,
            "source_type": source_type,
            "extracted_text": extracted_text,
            "llm_raw_response": llm_response,
            "entities": [e.to_dict() for e in result.entities],
            "quality": {
                "completeness": result.quality.completeness,
                "avg_confidence": result.quality.avg_confidence,
                "counts": {
                    "total": result.quality.counts.total,
                    "high": result.quality.counts.high,
                    "med": result.quality.counts.med,
                    "low": result.quality.counts.low,
                },
            },
            "validation": {
                "passed": result.validation.passed,
                "issues": result.validation.issues,
            },
            "meta": {
                "doc_type": result.meta.doc_type,
                "therapeutic_areas": result.meta.therapeutic_areas,
                "drug_density": result.meta.drug_density.value,
                "total_entities": result.meta.total_entities,
            },
            "model_used": result.model_used,
            "tokens_used": result.tokens_used,
            "status": "completed",
            "created_at": now,
            "updated_at": now,
        }

        await self._extraction_repo.save_extraction(extraction_doc)

        logger.info(
            "extraction_persisted",
            file_hash=file_hash,
            filename=filename,
            entities_count=len(result.entities),
        )

    def _build_personal_info_dict(self, personal_info: Any) -> dict[str, Any]:
        """Build personal_info dict from extraction PersonalInfo object."""
        return {
            "full_name": personal_info.full_name,
            "credentials": personal_info.credentials or [],
            "email": personal_info.email,
            "phone": personal_info.phone,
            "linkedin": personal_info.linkedin,
            "location": {
                "city": personal_info.location.city if personal_info.location else None,
                "state": personal_info.location.state if personal_info.location else None,
                "country": personal_info.location.country if personal_info.location else None,
            } if personal_info.location else None,
        }

    async def _get_or_create_profile(
        self,
        personal_info: Any,
        extraction_key: str,
    ) -> Profile | None:
        """Get existing profile or create new one from personal_info."""
        if not self._profile_repo:
            return None

        if not personal_info.full_name and not personal_info.email:
            return None

        personal_info_dict = self._build_personal_info_dict(personal_info)

        profile_key = generate_profile_key(
            email=personal_info_dict.get("email"),
            full_name=personal_info_dict.get("full_name"),
            linkedin=personal_info_dict.get("linkedin"),
        )

        existing_doc = await self._profile_repo.find_by_key(profile_key)
        if existing_doc:
            existing_profile = Profile.from_dict(existing_doc)
            if extraction_key not in existing_profile.source_extractions:
                existing_profile.source_extractions.append(extraction_key)
                await self._profile_repo.save_profile(existing_profile)
            await self._profile_repo.create_extraction_edge(existing_profile.key, extraction_key)
            return existing_profile

        profile = Profile.from_personal_info(personal_info_dict, extraction_key)
        saved_profile = await self._profile_repo.save_profile(profile)

        await self._profile_repo.create_extraction_edge(saved_profile.key, extraction_key)

        logger.info(
            "profile_created",
            profile_key=saved_profile.key,
            full_name=saved_profile.full_name,
            extraction_key=extraction_key,
        )

        return saved_profile

    async def _persist_profile(
        self,
        personal_info: Any,
        extraction_key: str,
    ) -> Profile | None:
        """Persist profile from extraction personal_info (called from extract_from_text)."""
        return await self._get_or_create_profile(personal_info, extraction_key)

    async def _get_cached_extraction(self, file_hash: str) -> ExtractionResult | None:
        """Check cache for existing extraction result."""
        if not self._extraction_repo:
            return None

        cached = await self._extraction_repo.find_by_file_hash(file_hash)
        if not cached:
            return None

        logger.info(
            "ner_extraction_cache_hit",
            file_hash=file_hash,
            entities_count=len(cached.get("entities", [])),
        )

        return ExtractionResult.from_cached(cached)

    def _parse_response(self, content: str) -> dict[str, Any]:
        """Parse LLM response as JSON."""
        content = content.strip()

        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("ner_json_parse_failed", error=str(e), content_preview=content[:200])
            raise ExtractionFailedError(reason=f"Failed to parse LLM response as JSON: {e}")

    async def extract_and_enrich(
        self,
        text: str,
        substance_service: SubstanceService,
        filename: str | None = None,
    ) -> ExtractAndEnrichResult:
        """
        Extract substances from text and enrich each with FDA data.

        This method is designed for the /extract endpoint flow:
        1. NER extraction from text
        2. Check which substances already exist (enriched) in DB
        3. Enrich only missing substances via SubstanceService
        4. Return complete result with NER, profile, and substances

        Args:
            text: Document text to process
            substance_service: SubstanceService instance for enrichment
            filename: Optional filename for reference

        Returns:
            ExtractAndEnrichResult with extraction, profile, and substances
        """
        text_bytes = text.encode("utf-8")
        file_hash = compute_file_hash(text_bytes)

        ner_result = await self.extract_from_text(text, filename)

        profile: Profile | None = None
        if self._profile_repo:
            profile = await self._profile_repo.find_by_extraction(file_hash)
            if not profile and ner_result.personal_info:
                profile = await self._get_or_create_profile(ner_result.personal_info, file_hash)

        substance_names = list({
            e.name for e in ner_result.entities
            if e.type in (EntityType.BRAND, EntityType.GENERIC)
        })

        if not substance_names:
            return ExtractAndEnrichResult(
                extraction_id=file_hash,
                extraction_result=ner_result,
                profile=profile,
                substances=[],
            )

        existing_substances = await substance_service.find_enriched_by_names(substance_names)

        names_to_enrich = [
            name for name in substance_names
            if name.lower() not in existing_substances
        ]

        logger.info(
            "extract_and_enrich_check",
            total_substances=len(substance_names),
            already_enriched=len(existing_substances),
            to_enrich=len(names_to_enrich),
        )

        enriched_results: dict[str, str] = {}

        if names_to_enrich:
            tasks = [substance_service.enrich_substance(name) for name in names_to_enrich]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for name, result in zip(names_to_enrich, results, strict=True):
                if isinstance(result, Exception):
                    logger.warning("enrichment_failed", substance_name=name, error=str(result))
                    continue

                if not result.found:
                    logger.warning("enrichment_not_found", substance_name=name)
                    continue

                substance_key = self._find_substance_key(name, result)
                if substance_key:
                    enriched_results[name.lower()] = substance_key

        refs: list[ExtractedSubstanceReference] = []
        substance_keys_found: list[str] = []

        for name in substance_names:
            name_lower = name.lower()

            if name_lower in existing_substances:
                substance = existing_substances[name_lower]
                refs.append(ExtractedSubstanceReference(
                    name=name,
                    substance_id=substance.key,
                    url=f"entity/{substance.key}",
                ))
                substance_keys_found.append(substance.key)
            elif name_lower in enriched_results:
                substance_key = enriched_results[name_lower]
                refs.append(ExtractedSubstanceReference(
                    name=name,
                    substance_id=substance_key,
                    url=f"entity/{substance_key}",
                ))
                substance_keys_found.append(substance_key)

        if self._profile_repo and profile and substance_keys_found:
            await self._profile_repo.create_substance_edges_bulk(
                profile.key,
                substance_keys_found,
            )
            logger.info(
                "profile_substance_edges_created",
                profile_key=profile.key,
                substances_count=len(substance_keys_found),
            )

        return ExtractAndEnrichResult(
            extraction_id=file_hash,
            extraction_result=ner_result,
            profile=profile,
            substances=refs,
        )

    # NOTE: _create_profile_substance_edges is no longer used - logic moved to extract_and_enrich
    # async def _create_profile_substance_edges(
    #     self,
    #     ner_result: ExtractionResult,
    #     substance_keys: list[str],
    # ) -> None:
    #     """Create edges between profile and substances found in extraction."""
    #     if not self._profile_repo or not ner_result.personal_info:
    #         return
    #
    #     if not ner_result.personal_info.full_name and not ner_result.personal_info.email:
    #         return
    #
    #     personal_info_dict = {
    #         "full_name": ner_result.personal_info.full_name,
    #         "email": ner_result.personal_info.email,
    #     }
    #
    #     profile_key = generate_profile_key(
    #         personal_info_dict.get("email"),
    #         personal_info_dict.get("full_name"),
    #     )
    #
    #     edges_created = await self._profile_repo.create_substance_edges_bulk(
    #         profile_key,
    #         substance_keys,
    #     )
    #
    #     if edges_created > 0:
    #         logger.info(
    #             "profile_substance_edges_created",
    #             profile_key=profile_key,
    #             substances_count=edges_created,
    #         )

    def _find_substance_key(self, search_name: str, graph_data) -> str | None:
        """
        Find the substance key that matches the search name.

        Priority:
        1. Exact match on substance name
        2. Key derived from search name
        """
        search_lower = search_name.lower()
        substance_key = search_lower.replace(" ", "_").replace("-", "_")

        for key, substance in graph_data.substances.items():
            if substance.name.lower() == search_lower:
                return key

        if substance_key in graph_data.substances:
            return substance_key

        return next(iter(graph_data.substances.keys()), None)
