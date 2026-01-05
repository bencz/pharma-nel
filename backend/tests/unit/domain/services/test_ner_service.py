"""
Unit tests for NERService.

Uses mocks for LLM client and extraction repository.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.extraction import EntityType, ExtractionResult
from src.domain.exceptions.extraction import ExtractionFailedError
from src.domain.ports.clients import LLMResponse
from src.domain.services.ner_service import NERService, compute_file_hash


class TestComputeFileHash:
    """Unit tests for compute_file_hash function."""

    def test_returns_32_char_hash(self) -> None:
        content = b"test content"
        result = compute_file_hash(content)
        assert len(result) == 32

    def test_same_content_same_hash(self) -> None:
        content = b"same content"
        hash1 = compute_file_hash(content)
        hash2 = compute_file_hash(content)
        assert hash1 == hash2

    def test_different_content_different_hash(self) -> None:
        hash1 = compute_file_hash(b"content 1")
        hash2 = compute_file_hash(b"content 2")
        assert hash1 != hash2


class TestNERService:
    """Unit tests for NERService."""

    @pytest.fixture
    def mock_llm_client(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_extraction_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_profile_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(
        self,
        mock_llm_client: AsyncMock,
        mock_extraction_repo: AsyncMock,
        mock_profile_repo: AsyncMock,
    ) -> NERService:
        return NERService(
            llm_client=mock_llm_client,
            extraction_repository=mock_extraction_repo,
            profile_repository=mock_profile_repo,
        )

    @pytest.fixture
    def service_no_repo(self, mock_llm_client: AsyncMock) -> NERService:
        return NERService(llm_client=mock_llm_client, extraction_repository=None, profile_repository=None)

    def _create_llm_response(self, entities: list[dict]) -> LLMResponse:
        """Helper to create mock LLM response."""
        content = json.dumps({
            "entities": entities,
            "quality": {
                "completeness": "complete",
                "avg_confidence": 0.9,
                "counts": {"total": len(entities), "high": len(entities), "med": 0, "low": 0},
            },
            "validation": {"passed": True, "issues": []},
            "meta": {
                "doc_type": "resume",
                "therapeutic_areas": ["cardiology"],
                "drug_density": "MED",
                "total_entities": len(entities),
            },
        })
        return LLMResponse(
            content=content,
            model="gpt-4o-mini",
            usage={"total_tokens": 500, "input_tokens": 300, "output_tokens": 200},
        )

    async def test_extract_from_text_success(
        self,
        service: NERService,
        mock_llm_client: AsyncMock,
        mock_extraction_repo: AsyncMock,
        mock_profile_repo: AsyncMock,
    ) -> None:
        mock_extraction_repo.find_by_file_hash = AsyncMock(return_value=None)

        entities = [
            {"name": "Aspirin", "type": "BRAND", "confidence": 0.95},
            {"name": "Ibuprofen", "type": "GENERIC", "confidence": 0.90},
        ]
        mock_llm_client.complete.return_value = self._create_llm_response(entities)

        result = await service.extract_from_text("Patient takes Aspirin and Ibuprofen")

        assert isinstance(result, ExtractionResult)
        assert len(result.entities) == 2
        mock_llm_client.complete.assert_called_once()
        mock_extraction_repo.save_extraction.assert_called_once()

    async def test_extract_from_text_cache_hit(
        self,
        service: NERService,
        mock_llm_client: AsyncMock,
        mock_extraction_repo: AsyncMock,
        mock_profile_repo: AsyncMock,
    ) -> None:
        cached_data = {
            "entities": [{"name": "CachedDrug", "type": "BRAND", "confidence": 0.9}],
            "quality": {"completeness": "complete", "avg_confidence": 0.9, "counts": {"total": 1, "high": 1, "med": 0, "low": 0}},
            "validation": {"passed": True, "issues": []},
            "meta": {"doc_type": "resume", "therapeutic_areas": [], "drug_density": "LOW", "total_entities": 1},
            "model_used": "gpt-4o-mini",
            "tokens_used": 100,
        }
        mock_extraction_repo.find_by_file_hash = AsyncMock(return_value=cached_data)

        result = await service.extract_from_text("Some text")

        assert isinstance(result, ExtractionResult)
        mock_llm_client.complete.assert_not_called()
        mock_extraction_repo.save_extraction.assert_not_called()

    async def test_extract_from_text_no_repo(
        self,
        service_no_repo: NERService,
        mock_llm_client: AsyncMock,
    ) -> None:
        entities = [{"name": "TestDrug", "type": "BRAND", "confidence": 0.85}]
        mock_llm_client.complete.return_value = self._create_llm_response(entities)

        result = await service_no_repo.extract_from_text("Test text")

        assert isinstance(result, ExtractionResult)
        assert len(result.entities) == 1

    async def test_extract_from_text_json_parse_error(
        self,
        service_no_repo: NERService,
        mock_llm_client: AsyncMock,
    ) -> None:
        mock_llm_client.complete.return_value = LLMResponse(
            content="invalid json {{{",
            model="gpt-4o-mini",
            usage={"total_tokens": 100},
        )

        with pytest.raises(ExtractionFailedError):
            await service_no_repo.extract_from_text("Test text")

    async def test_parse_response_strips_markdown(
        self,
        service_no_repo: NERService,
    ) -> None:
        content = '```json\n{"entities": [], "quality": {"completeness": "complete", "avg_confidence": 0, "counts": {"total": 0, "high": 0, "med": 0, "low": 0}}, "validation": {"passed": true, "issues": []}, "meta": {"doc_type": "unknown", "therapeutic_areas": [], "drug_density": "none", "total_entities": 0}}\n```'
        result = service_no_repo._parse_response(content)
        assert "entities" in result


class TestNERServiceExtractAndEnrich:
    """Unit tests for extract_and_enrich method."""

    @pytest.fixture
    def mock_llm_client(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_extraction_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_profile_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_substance_service(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(
        self,
        mock_llm_client: AsyncMock,
        mock_extraction_repo: AsyncMock,
        mock_profile_repo: AsyncMock,
    ) -> NERService:
        return NERService(
            llm_client=mock_llm_client,
            extraction_repository=mock_extraction_repo,
            profile_repository=mock_profile_repo,
        )

    def _create_llm_response(self, entities: list[dict]) -> LLMResponse:
        content = json.dumps({
            "entities": entities,
            "quality": {"completeness": "complete", "avg_confidence": 0.9, "counts": {"total": len(entities), "high": len(entities), "med": 0, "low": 0}},
            "validation": {"passed": True, "issues": []},
            "meta": {"doc_type": "resume", "therapeutic_areas": [], "drug_density": "MED", "total_entities": len(entities)},
        })
        return LLMResponse(content=content, model="gpt-4o-mini", usage={"total_tokens": 500})

    async def test_extract_and_enrich_with_existing_substances(
        self,
        service: NERService,
        mock_llm_client: AsyncMock,
        mock_extraction_repo: AsyncMock,
        mock_profile_repo: AsyncMock,
        mock_substance_service: AsyncMock,
    ) -> None:
        mock_extraction_repo.find_by_file_hash = AsyncMock(return_value=None)
        mock_profile_repo.find_by_key = AsyncMock(return_value=None)
        mock_profile_repo.save = AsyncMock(return_value=None)
        mock_profile_repo.create_extraction_edge = AsyncMock(return_value=None)
        mock_profile_repo.create_substance_interest_edge = AsyncMock(return_value=None)

        entities = [
            {"name": "Aspirin", "type": "BRAND", "confidence": 0.95},
            {"name": "Ibuprofen", "type": "GENERIC", "confidence": 0.90},
        ]
        mock_llm_client.complete.return_value = self._create_llm_response(entities)

        existing_substance = MagicMock()
        existing_substance.key = "aspirin"
        mock_substance_service.find_enriched_by_names = AsyncMock(return_value={
            "aspirin": existing_substance,
        })

        graph_data = MagicMock()
        graph_data.found = True
        graph_data.substances = {"ibuprofen": MagicMock(name="ibuprofen")}
        mock_substance_service.enrich_substance = AsyncMock(return_value=graph_data)

        result = await service.extract_and_enrich(
            "Patient takes Aspirin and Ibuprofen",
            mock_substance_service,
        )

        assert len(result.substances) == 2
        mock_substance_service.find_enriched_by_names.assert_called_once()
        mock_substance_service.enrich_substance.assert_called_once()

    async def test_extract_and_enrich_no_substances(
        self,
        service: NERService,
        mock_llm_client: AsyncMock,
        mock_extraction_repo: AsyncMock,
        mock_profile_repo: AsyncMock,
        mock_substance_service: AsyncMock,
    ) -> None:
        mock_extraction_repo.find_by_file_hash = AsyncMock(return_value=None)
        mock_profile_repo.find_by_key = AsyncMock(return_value=None)
        mock_profile_repo.save = AsyncMock(return_value=None)
        mock_profile_repo.create_extraction_edge = AsyncMock(return_value=None)

        entities = [{"name": "SomeCode", "type": "CODE", "confidence": 0.8}]
        mock_llm_client.complete.return_value = self._create_llm_response(entities)

        result = await service.extract_and_enrich("Document with code", mock_substance_service)

        assert len(result.substances) == 0
        mock_substance_service.find_enriched_by_names.assert_not_called()
