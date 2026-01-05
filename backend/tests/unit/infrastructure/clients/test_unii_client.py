"""
Unit tests for UNIIClient.

Tests UNII/Substance API interactions with mocked HTTP responses.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.clients.unii_client import ChemicalData, UNIIClient, UNIIClientConfig


class TestChemicalData:
    """Unit tests for ChemicalData dataclass."""

    def test_to_dict(self) -> None:
        data = ChemicalData(
            unii="R16CO5Y76E",
            name="ASPIRIN",
            formula="C9H8O4",
            molecular_weight=180.16,
            smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
        )

        result = data.to_dict()

        assert result["unii"] == "R16CO5Y76E"
        assert result["name"] == "ASPIRIN"
        assert result["formula"] == "C9H8O4"
        assert result["molecular_weight"] == 180.16

    def test_default_values(self) -> None:
        data = ChemicalData()

        assert data.unii is None
        assert data.names == []


class TestUNIIClient:
    """Unit tests for UNIIClient."""

    @pytest.fixture
    def client(self) -> UNIIClient:
        config = UNIIClientConfig(
            base_url="https://api.fda.gov/other/substance.json",
            timeout=10.0,
            max_retries=1,
        )
        return UNIIClient(config)

    async def test_unii_request_success(self, client: UNIIClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"unii": "test"}]}

        with patch.object(client, "get", return_value=mock_response):
            result = await client._unii_request({"search": "test"})

        assert result == {"results": [{"unii": "test"}]}

    async def test_unii_request_404_returns_none(self, client: UNIIClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client, "get", return_value=mock_response):
            result = await client._unii_request({"search": "test"})

        assert result is None

    async def test_unii_request_not_found_in_response(self, client: UNIIClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": {"code": "NOT_FOUND"}}

        with patch.object(client, "get", return_value=mock_response):
            result = await client._unii_request({"search": "test"})

        assert result is None

    def test_extract_chemical_data_full(self, client: UNIIClient) -> None:
        record = {
            "unii": "R16CO5Y76E",
            "substance_class": "Chemical",
            "definition_type": "PRIMARY",
            "names": [
                {"name": "ASPIRIN", "display_name": True},
                {"name": "ACETYLSALICYLIC ACID"},
            ],
            "structure": {
                "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
                "formula": "C9H8O4",
                "mwt": "180.16",
                "stereochemistry": "ACHIRAL",
            },
            "codes": [
                {"code_system": "CAS", "code": "50-78-2"},
                {"code_system": "PUBCHEM", "code": "2244"},
                {"code_system": "INCHIKEY", "code": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"},
            ],
        }

        result = client._extract_chemical_data(record)

        assert result.unii == "R16CO5Y76E"
        assert result.name == "ASPIRIN"
        assert result.formula == "C9H8O4"
        assert result.molecular_weight == 180.16
        assert result.smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
        assert result.cas_number == "50-78-2"
        assert result.pubchem_id == "2244"
        assert result.inchi_key == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
        assert "ASPIRIN" in result.names

    def test_extract_chemical_data_minimal(self, client: UNIIClient) -> None:
        record = {"unii": "TEST123"}

        result = client._extract_chemical_data(record)

        assert result.unii == "TEST123"
        assert result.name is None
        assert result.names == []

    def test_extract_chemical_data_from_moieties(self, client: UNIIClient) -> None:
        record = {
            "unii": "TEST456",
            "moieties": [
                {"smiles": "C1=CC=CC=C1", "formula": "C6H6"},
            ],
        }

        result = client._extract_chemical_data(record)

        assert result.smiles == "C1=CC=CC=C1"
        assert result.formula == "C6H6"

    def test_extract_chemical_data_invalid_molecular_weight(self, client: UNIIClient) -> None:
        record = {
            "unii": "TEST789",
            "structure": {"mwt": "invalid"},
        }

        result = client._extract_chemical_data(record)

        assert result.molecular_weight is None

    async def test_search_by_unii_found(self, client: UNIIClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"unii": "R16CO5Y76E", "names": [{"name": "ASPIRIN"}]}]
        }

        with patch.object(client, "get", return_value=mock_response):
            result = await client.search_by_unii("R16CO5Y76E")

        assert result is not None
        assert result.unii == "R16CO5Y76E"

    async def test_search_by_unii_not_found(self, client: UNIIClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client, "get", return_value=mock_response):
            result = await client.search_by_unii("NONEXISTENT")

        assert result is None

    async def test_search_by_name(self, client: UNIIClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"unii": "R16CO5Y76E", "names": [{"name": "ASPIRIN"}]},
                {"unii": "OTHER123", "names": [{"name": "ASPIRIN DERIVATIVE"}]},
            ]
        }

        with patch.object(client, "get", return_value=mock_response):
            results = await client.search_by_name("aspirin", limit=5)

        assert len(results) == 2

    async def test_search_by_name_empty(self, client: UNIIClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client, "get", return_value=mock_response):
            results = await client.search_by_name("nonexistent")

        assert results == []

    async def test_search_by_cas(self, client: UNIIClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"unii": "R16CO5Y76E", "codes": [{"code_system": "CAS", "code": "50-78-2"}]}]
        }

        with patch.object(client, "get", return_value=mock_response):
            result = await client.search_by_cas("50-78-2")

        assert result is not None

    async def test_get_substance_data_by_unii(self, client: UNIIClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"unii": "R16CO5Y76E"}]
        }

        with patch.object(client, "get", return_value=mock_response):
            result = await client.get_substance_data(unii="R16CO5Y76E")

        assert result is not None
        assert result.unii == "R16CO5Y76E"

    async def test_get_substance_data_by_name_fallback(self, client: UNIIClient) -> None:
        mock_unii_response = MagicMock()
        mock_unii_response.status_code = 404

        mock_name_response = MagicMock()
        mock_name_response.status_code = 200
        mock_name_response.json.return_value = {
            "results": [{"unii": "FOUND123", "names": [{"name": "TEST"}]}]
        }

        with patch.object(client, "get") as mock_get:
            mock_get.side_effect = [mock_unii_response, mock_name_response]

            result = await client.get_substance_data(unii="NOTFOUND", name="TEST")

        assert result is not None
        assert result.unii == "FOUND123"

    async def test_get_substance_data_not_found(self, client: UNIIClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client, "get", return_value=mock_response):
            result = await client.get_substance_data(unii="NOTFOUND", name="NOTFOUND")

        assert result is None

    async def test_get_multiple_substances(self, client: UNIIClient) -> None:
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {"results": [{"unii": "UNII1"}]}

        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"results": [{"unii": "UNII2"}]}

        with patch.object(client, "get") as mock_get:
            mock_get.side_effect = [mock_response1, mock_response2]

            results = await client.get_multiple_substances([
                {"unii": "UNII1"},
                {"name": "Drug2"},
            ])

        assert len(results) == 2

    async def test_get_multiple_substances_handles_errors(self, client: UNIIClient) -> None:
        mock_success = MagicMock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"results": [{"unii": "SUCCESS"}]}

        mock_error = MagicMock()
        mock_error.status_code = 500

        with patch.object(client, "get") as mock_get:
            mock_get.side_effect = [mock_success, mock_error]

            results = await client.get_multiple_substances([
                {"unii": "SUCCESS"},
                {"unii": "ERROR"},
            ])

        assert len(results) == 1
        assert "SUCCESS" in results
