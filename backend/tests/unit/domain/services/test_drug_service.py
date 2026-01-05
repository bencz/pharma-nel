"""
Unit tests for DrugService.

Uses mocks for repositories.
"""

from unittest.mock import AsyncMock

import pytest

from src.domain.entities.drug import Drug
from src.domain.exceptions.drug import DrugNotFoundError
from src.domain.services.drug_service import DrugService


class TestDrugService:
    """Unit tests for DrugService."""

    @pytest.fixture
    def mock_drug_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_graph_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(
        self,
        mock_drug_repo: AsyncMock,
        mock_graph_repo: AsyncMock,
    ) -> DrugService:
        return DrugService(
            drug_repository=mock_drug_repo,
            graph_repository=mock_graph_repo,
        )

    async def test_get_by_key_found(
        self,
        service: DrugService,
        mock_drug_repo: AsyncMock,
    ) -> None:
        mock_drug_repo.find_by_key.return_value = Drug(
            key="test_key",
            brand_names=["TestBrand"],
            is_enriched=True,
        )

        result = await service.get_by_key("test_key")

        assert result.key == "test_key"
        assert result.is_enriched is True
        mock_drug_repo.find_by_key.assert_called_once_with("test_key")

    async def test_get_by_key_not_found_raises(
        self,
        service: DrugService,
        mock_drug_repo: AsyncMock,
    ) -> None:
        mock_drug_repo.find_by_key.return_value = None

        with pytest.raises(DrugNotFoundError):
            await service.get_by_key("nonexistent")

    async def test_get_by_name_found(
        self,
        service: DrugService,
        mock_drug_repo: AsyncMock,
    ) -> None:
        mock_drug_repo.find_by_name.return_value = Drug(
            key="name_key",
            brand_names=["NameBrand"],
            is_enriched=True,
        )

        result = await service.get_by_name("NameBrand")

        assert result.brand_names == ["NameBrand"]
        mock_drug_repo.find_by_name.assert_called_once_with("NameBrand")

    async def test_get_by_name_not_found_raises(
        self,
        service: DrugService,
        mock_drug_repo: AsyncMock,
    ) -> None:
        mock_drug_repo.find_by_name.return_value = None

        with pytest.raises(DrugNotFoundError):
            await service.get_by_name("NonexistentDrug")

    async def test_get_by_rxcui_found(
        self,
        service: DrugService,
        mock_drug_repo: AsyncMock,
    ) -> None:
        mock_drug_repo.find_by_rxcui.return_value = Drug(
            key="rxcui_key",
            brand_names=["RxCuiBrand"],
            rxcui=["12345"],
        )

        result = await service.get_by_rxcui("12345")

        assert result.rxcui == ["12345"]
        mock_drug_repo.find_by_rxcui.assert_called_once_with("12345")

    async def test_get_by_rxcui_not_found_raises(
        self,
        service: DrugService,
        mock_drug_repo: AsyncMock,
    ) -> None:
        mock_drug_repo.find_by_rxcui.return_value = None

        with pytest.raises(DrugNotFoundError):
            await service.get_by_rxcui("99999")

    async def test_search_delegates_to_repo(
        self,
        service: DrugService,
        mock_drug_repo: AsyncMock,
    ) -> None:
        mock_drug_repo.search.return_value = [
            Drug(key="search1", brand_names=["Search1"]),
            Drug(key="search2", brand_names=["Search2"]),
        ]

        results = await service.search("Search", limit=10)

        assert len(results) == 2
        mock_drug_repo.search.assert_called_once_with("Search", 10)

    async def test_search_empty_results(
        self,
        service: DrugService,
        mock_drug_repo: AsyncMock,
    ) -> None:
        mock_drug_repo.search.return_value = []

        results = await service.search("NonexistentTerm", limit=10)

        assert len(results) == 0
        mock_drug_repo.search.assert_called_once_with("NonexistentTerm", 10)

    async def test_get_with_relations_delegates_to_graph_repo(
        self,
        service: DrugService,
        mock_graph_repo: AsyncMock,
    ) -> None:
        mock_graph_repo.get_drug_with_relations.return_value = {
            "drug": {"_key": "rel_key"},
            "substances": [],
        }

        result = await service.get_with_relations("rel_key")

        assert result is not None
        assert result["drug"]["_key"] == "rel_key"
        mock_graph_repo.get_drug_with_relations.assert_called_once_with("rel_key")

    async def test_get_with_relations_not_found(
        self,
        service: DrugService,
        mock_graph_repo: AsyncMock,
    ) -> None:
        mock_graph_repo.get_drug_with_relations.return_value = None

        result = await service.get_with_relations("nonexistent_key")

        assert result is None
        mock_graph_repo.get_drug_with_relations.assert_called_once_with("nonexistent_key")
