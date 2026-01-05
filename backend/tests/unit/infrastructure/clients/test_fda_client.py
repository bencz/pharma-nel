"""
Unit tests for FDAClient.

Tests FDA API interactions with mocked HTTP responses.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.clients.fda_client import FDAClient, FDAClientConfig


class TestFDAClient:
    """Unit tests for FDAClient."""

    @pytest.fixture
    def client(self) -> FDAClient:
        config = FDAClientConfig(
            base_url="https://api.fda.gov",
            api_key="test_api_key",
            timeout=10.0,
            max_retries=1,
        )
        return FDAClient(config)

    @pytest.fixture
    def client_no_key(self) -> FDAClient:
        config = FDAClientConfig(base_url="https://api.fda.gov", api_key=None)
        return FDAClient(config)

    def test_build_search_query_default(self, client: FDAClient) -> None:
        query = client._build_search_query("aspirin")
        assert 'openfda.brand_name:"aspirin"' in query
        assert 'openfda.generic_name:"aspirin"' in query
        assert 'openfda.substance_name:"aspirin"' in query

    def test_build_search_query_with_field(self, client: FDAClient) -> None:
        query = client._build_search_query("aspirin", field="openfda.brand_name")
        assert query == 'openfda.brand_name:"aspirin"'

    def test_build_search_query_escapes_quotes(self, client: FDAClient) -> None:
        query = client._build_search_query('test"drug', field="openfda.brand_name")
        assert '\\"' in query

    async def test_fda_request_success(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"data": "test"}]}

        with patch.object(client, "get", return_value=mock_response):
            result = await client._fda_request("/drug/drugsfda.json", {"search": "test"})

        assert result == {"results": [{"data": "test"}]}

    async def test_fda_request_404_returns_none(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client, "get", return_value=mock_response):
            result = await client._fda_request("/drug/drugsfda.json", {"search": "test"})

        assert result is None

    async def test_fda_request_adds_api_key(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            await client._fda_request("/test", {"search": "test"})

            call_args = mock_get.call_args
            assert call_args[1]["params"]["api_key"] == "test_api_key"

    async def test_fda_request_no_api_key(self, client_no_key: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        with patch.object(client_no_key, "get", return_value=mock_response) as mock_get:
            await client_no_key._fda_request("/test", {"search": "test"})

            call_args = mock_get.call_args
            assert "api_key" not in call_args[1]["params"]

    async def test_search_drugsfda(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"application_number": "NDA123456"}]
        }

        with patch.object(client, "get", return_value=mock_response):
            results = await client.search_drugsfda("aspirin")

        assert len(results) == 1
        assert results[0]["application_number"] == "NDA123456"

    async def test_search_drugsfda_empty(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client, "get", return_value=mock_response):
            results = await client.search_drugsfda("nonexistent")

        assert results == []

    async def test_search_labels(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"spl_id": "test-spl-id"}]
        }

        with patch.object(client, "get", return_value=mock_response):
            results = await client.search_labels("aspirin")

        assert len(results) == 1

    async def test_get_label_by_spl_id(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"spl_id": "test-spl", "description": ["Test description"]}]
        }

        with patch.object(client, "get", return_value=mock_response):
            result = await client.get_label_by_spl_id("test-spl")

        assert result is not None
        assert result["spl_id"] == "test-spl"

    async def test_get_label_by_spl_id_not_found(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client, "get", return_value=mock_response):
            result = await client.get_label_by_spl_id("nonexistent")

        assert result is None

    async def test_search_ndc(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"product_ndc": "12345-678-90"}]
        }

        with patch.object(client, "get", return_value=mock_response):
            results = await client.search_ndc("aspirin")

        assert len(results) == 1

    async def test_search_adverse_events(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"patient": {"drug": []}}]
        }

        with patch.object(client, "get", return_value=mock_response):
            results = await client.search_adverse_events("aspirin", limit=10)

        assert len(results) == 1

    async def test_search_adverse_events_serious_filter(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            await client.search_adverse_events("aspirin", serious=True)

            call_args = mock_get.call_args
            assert "serious:1" in call_args[1]["params"]["search"]

    async def test_search_enforcement(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"recall_number": "R-123"}]
        }

        with patch.object(client, "get", return_value=mock_response):
            results = await client.search_enforcement("aspirin")

        assert len(results) == 1

    async def test_get_all_drug_data(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"data": "test"}]}

        with patch.object(client, "get", return_value=mock_response):
            data = await client.get_all_drug_data("aspirin", include_events=True)

        assert "drugsfda" in data
        assert "ndc" in data
        assert "enforcement" in data
        assert "events" in data

    async def test_get_all_drug_data_without_events(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        with patch.object(client, "get", return_value=mock_response):
            data = await client.get_all_drug_data("aspirin", include_events=False)

        assert "drugsfda" in data
        assert "events" not in data

    async def test_limit_capped_at_max(self, client: FDAClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            await client.search_drugsfda("aspirin", limit=5000)

            call_args = mock_get.call_args
            assert call_args[1]["params"]["limit"] == 1000
