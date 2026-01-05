"""
Unit tests for SubstanceService.

Uses mocks for repositories and enrichment service.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.pharma_graph import SubstanceGraphData
from src.domain.entities.substance import Substance
from src.domain.exceptions.drug import SubstanceNotFoundError
from src.domain.services.substance_service import SubstanceService


class TestSubstanceService:
    """Unit tests for SubstanceService."""

    @pytest.fixture
    def mock_substance_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_graph_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_enrichment(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(
        self,
        mock_substance_repo: AsyncMock,
        mock_graph_repo: AsyncMock,
        mock_enrichment: AsyncMock,
    ) -> SubstanceService:
        return SubstanceService(
            substance_repository=mock_substance_repo,
            graph_repository=mock_graph_repo,
            enrichment_service=mock_enrichment,
        )

    @pytest.fixture
    def service_no_enrichment(
        self,
        mock_substance_repo: AsyncMock,
        mock_graph_repo: AsyncMock,
    ) -> SubstanceService:
        return SubstanceService(
            substance_repository=mock_substance_repo,
            graph_repository=mock_graph_repo,
            enrichment_service=None,
        )

    async def test_get_by_key_found(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
    ) -> None:
        mock_substance_repo.find_by_key.return_value = Substance(
            key="ibuprofen",
            name="IBUPROFEN",
            is_enriched=True,
        )

        result = await service.get_by_key("ibuprofen")

        assert result.key == "ibuprofen"
        mock_substance_repo.find_by_key.assert_called_once_with("ibuprofen")

    async def test_get_by_key_fallback_to_name(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
    ) -> None:
        mock_substance_repo.find_by_key.return_value = None
        mock_substance_repo.find_by_name.return_value = Substance(
            key="ibuprofen",
            name="IBUPROFEN",
        )

        result = await service.get_by_key("IBUPROFEN")

        assert result.key == "ibuprofen"
        mock_substance_repo.find_by_name.assert_called_once_with("IBUPROFEN")

    async def test_get_by_key_not_found_raises(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
    ) -> None:
        mock_substance_repo.find_by_key.return_value = None
        mock_substance_repo.find_by_name.return_value = None

        with pytest.raises(SubstanceNotFoundError):
            await service.get_by_key("nonexistent")

    async def test_get_by_name_found(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
    ) -> None:
        mock_substance_repo.find_by_name.return_value = Substance(
            key="aspirin",
            name="ASPIRIN",
        )

        result = await service.get_by_name("ASPIRIN")

        assert result.name == "ASPIRIN"
        mock_substance_repo.find_by_name.assert_called_once_with("ASPIRIN")

    async def test_get_by_name_fallback_to_key(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
    ) -> None:
        mock_substance_repo.find_by_name.return_value = None
        mock_substance_repo.find_by_key.return_value = Substance(
            key="aspirin",
            name="ASPIRIN",
        )

        result = await service.get_by_name("aspirin")

        assert result.key == "aspirin"

    async def test_get_by_name_not_found_raises(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
    ) -> None:
        mock_substance_repo.find_by_name.return_value = None
        mock_substance_repo.find_by_key.return_value = None

        with pytest.raises(SubstanceNotFoundError):
            await service.get_by_name("nonexistent")

    async def test_get_profile_found(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
        mock_graph_repo: AsyncMock,
    ) -> None:
        substance = Substance(key="ibuprofen", name="IBUPROFEN")
        mock_substance_repo.find_by_key.return_value = substance
        mock_graph_repo.get_substance_relations.return_value = {
            "drugs": [{"key": "advil", "brand_names": ["Advil"]}],
            "pharm_classes": [],
        }

        result = await service.get_profile("ibuprofen")

        assert result["substance"] == substance
        assert "drugs" in result["relations"]
        mock_graph_repo.get_substance_relations.assert_called_once_with("ibuprofen")

    async def test_get_profile_fallback_to_name(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
        mock_graph_repo: AsyncMock,
    ) -> None:
        mock_substance_repo.find_by_key.return_value = None
        substance = Substance(key="ibuprofen", name="IBUPROFEN")
        mock_substance_repo.find_by_name.return_value = substance
        mock_graph_repo.get_substance_relations.return_value = {}

        result = await service.get_profile("IBUPROFEN")

        assert result["substance"] == substance

    async def test_get_profile_not_found_raises(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
    ) -> None:
        mock_substance_repo.find_by_key.return_value = None
        mock_substance_repo.find_by_name.return_value = None

        with pytest.raises(SubstanceNotFoundError):
            await service.get_profile("nonexistent")

    async def test_search_delegates_to_repo(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
    ) -> None:
        mock_substance_repo.search.return_value = [
            Substance(key="ibu1", name="IBUPROFEN"),
            Substance(key="ibu2", name="IBUPROFEN LYSINE"),
        ]

        results = await service.search("ibu", limit=10)

        assert len(results) == 2
        mock_substance_repo.search.assert_called_once_with("ibu", limit=10)

    async def test_enrich_substance_already_enriched(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
        mock_enrichment: AsyncMock,
    ) -> None:
        existing = Substance(key="aspirin", name="ASPIRIN", is_enriched=True)
        mock_substance_repo.find_enriched_by_name.return_value = existing

        result = await service.enrich_substance("aspirin")

        assert result.found is True
        assert "aspirin" in result.substances
        mock_enrichment.get_substance_data.assert_not_called()

    async def test_enrich_substance_triggers_enrichment(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
        mock_graph_repo: AsyncMock,
        mock_enrichment: AsyncMock,
    ) -> None:
        mock_substance_repo.find_enriched_by_name.return_value = None

        graph_data = SubstanceGraphData(search_term="newdrug", found=True)
        mock_enrichment.get_substance_data.return_value = graph_data
        mock_graph_repo.persist_graph_data.return_value = {"substances": 1}

        result = await service.enrich_substance("newdrug")

        assert result.found is True
        mock_enrichment.get_substance_data.assert_called_once()
        mock_graph_repo.persist_graph_data.assert_called_once()

    async def test_enrich_substance_force_re_enriches(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
        mock_graph_repo: AsyncMock,
        mock_enrichment: AsyncMock,
    ) -> None:
        graph_data = SubstanceGraphData(search_term="forcedrug", found=True)
        mock_enrichment.get_substance_data.return_value = graph_data
        mock_graph_repo.persist_graph_data.return_value = {"substances": 1}

        result = await service.enrich_substance("forcedrug", force=True)

        assert result.found is True
        mock_substance_repo.find_enriched_by_name.assert_not_called()
        mock_enrichment.get_substance_data.assert_called_once()

    async def test_enrich_substance_no_enrichment_service_raises(
        self,
        service_no_enrichment: SubstanceService,
    ) -> None:
        with pytest.raises(RuntimeError, match="requires enrichment_service"):
            await service_no_enrichment.enrich_substance("test")

    async def test_find_enriched_by_names_delegates(
        self,
        service: SubstanceService,
        mock_substance_repo: AsyncMock,
    ) -> None:
        mock_substance_repo.find_enriched_by_names.return_value = {
            "aspirin": Substance(key="aspirin", name="ASPIRIN"),
        }

        result = await service.find_enriched_by_names(["aspirin", "ibuprofen"])

        assert "aspirin" in result
        mock_substance_repo.find_enriched_by_names.assert_called_once_with(
            ["aspirin", "ibuprofen"]
        )
