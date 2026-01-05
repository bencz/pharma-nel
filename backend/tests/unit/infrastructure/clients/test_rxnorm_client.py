"""
Unit tests for RxNormClient.

Tests RxNorm API interactions with mocked HTTP responses.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.clients.rxnorm_client import RxNormClient, RxNormClientConfig


class TestRxNormClient:
    """Unit tests for RxNormClient."""

    @pytest.fixture
    def client(self) -> RxNormClient:
        config = RxNormClientConfig(
            base_url="https://rxnav.nlm.nih.gov/REST",
            timeout=10.0,
            max_retries=1,
        )
        return RxNormClient(config)

    async def test_rxnorm_request_success(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}

        with patch.object(client, "get", return_value=mock_response):
            result = await client._rxnorm_request("/test")

        assert result == {"data": "test"}

    async def test_rxnorm_request_404_returns_none(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client, "get", return_value=mock_response):
            result = await client._rxnorm_request("/test")

        assert result is None

    async def test_rxnorm_request_adds_json_format(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        with patch.object(client, "get", return_value=mock_response) as mock_get:
            await client._rxnorm_request("/test", {"param": "value"})

            call_args = mock_get.call_args
            assert call_args[1]["params"]["format"] == "json"

    async def test_get_rxcui_by_name_found(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "idGroup": {"rxnormId": ["1191", "1192"]}
        }

        with patch.object(client, "get", return_value=mock_response):
            results = await client.get_rxcui_by_name("aspirin")

        assert len(results) == 2
        assert results[0]["rxcui"] == "1191"

    async def test_get_rxcui_by_name_not_found(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"idGroup": {}}

        with patch.object(client, "get", return_value=mock_response):
            results = await client.get_rxcui_by_name("nonexistent")

        assert results == []

    async def test_approximate_match(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "approximateGroup": {
                "candidate": [
                    {"rxcui": "1191", "name": "aspirin", "score": "100", "rank": "1"},
                ]
            }
        }

        with patch.object(client, "get", return_value=mock_response):
            results = await client.approximate_match("asprin")

        assert len(results) == 1
        assert results[0]["rxcui"] == "1191"

    async def test_get_drug_info(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "properties": {"rxcui": "1191", "name": "aspirin", "tty": "IN"}
        }

        with patch.object(client, "get", return_value=mock_response):
            result = await client.get_drug_info("1191")

        assert result is not None
        assert result["rxcui"] == "1191"

    async def test_get_drug_info_not_found(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(client, "get", return_value=mock_response):
            result = await client.get_drug_info("99999")

        assert result is None

    async def test_get_related_drugs(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "allRelatedGroup": {
                "conceptGroup": [
                    {
                        "tty": "BN",
                        "conceptProperties": [
                            {"rxcui": "12345", "name": "Advil", "tty": "BN"}
                        ],
                    },
                    {
                        "tty": "IN",
                        "conceptProperties": [
                            {"rxcui": "5640", "name": "ibuprofen", "tty": "IN"}
                        ],
                    },
                ]
            }
        }

        with patch.object(client, "get", return_value=mock_response):
            results = await client.get_related_drugs("5640")

        assert "BN" in results
        assert "IN" in results
        assert results["BN"][0]["name"] == "Advil"

    async def test_get_ndc_codes(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ndcGroup": {"ndcList": {"ndc": ["12345-678-90", "12345-678-91"]}}
        }

        with patch.object(client, "get", return_value=mock_response):
            results = await client.get_ndc_codes("1191")

        assert len(results) == 2

    async def test_get_ndc_codes_empty(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ndcGroup": {}}

        with patch.object(client, "get", return_value=mock_response):
            results = await client.get_ndc_codes("1191")

        assert results == []

    async def test_get_drug_interactions(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "interactionTypeGroup": [
                {
                    "interactionType": [
                        {
                            "interactionPair": [
                                {
                                    "severity": "high",
                                    "description": "Test interaction",
                                    "interactionConcept": [
                                        {"minConceptItem": {"rxcui": "123", "name": "Drug A"}},
                                    ],
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        with patch.object(client, "get", return_value=mock_response):
            results = await client.get_drug_interactions("1191")

        assert len(results) == 1
        assert results[0]["severity"] == "high"

    async def test_get_spelling_suggestions(self, client: RxNormClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "suggestionGroup": {"suggestionList": {"suggestion": ["aspirin", "aspirine"]}}
        }

        with patch.object(client, "get", return_value=mock_response):
            results = await client.get_spelling_suggestions("asprin")

        assert "aspirin" in results

    async def test_get_all_drug_data_found(self, client: RxNormClient) -> None:
        mock_rxcui_response = MagicMock()
        mock_rxcui_response.status_code = 200
        mock_rxcui_response.json.return_value = {"idGroup": {"rxnormId": ["1191"]}}

        mock_info_response = MagicMock()
        mock_info_response.status_code = 200
        mock_info_response.json.return_value = {"properties": {"rxcui": "1191"}}

        mock_related_response = MagicMock()
        mock_related_response.status_code = 200
        mock_related_response.json.return_value = {"allRelatedGroup": {"conceptGroup": []}}

        mock_ndc_response = MagicMock()
        mock_ndc_response.status_code = 200
        mock_ndc_response.json.return_value = {"ndcGroup": {"ndcList": {"ndc": []}}}

        mock_interactions_response = MagicMock()
        mock_interactions_response.status_code = 200
        mock_interactions_response.json.return_value = {}

        with patch.object(client, "get") as mock_get:
            mock_get.side_effect = [
                mock_rxcui_response,
                mock_info_response,
                mock_related_response,
                mock_ndc_response,
                mock_interactions_response,
            ]

            result = await client.get_all_drug_data("aspirin")

        assert result["found"] is True
        assert result["rxcui"] == "1191"

    async def test_get_all_drug_data_not_found(self, client: RxNormClient) -> None:
        mock_rxcui_response = MagicMock()
        mock_rxcui_response.status_code = 200
        mock_rxcui_response.json.return_value = {"idGroup": {}}

        mock_approx_response = MagicMock()
        mock_approx_response.status_code = 200
        mock_approx_response.json.return_value = {"approximateGroup": {}}

        mock_spelling_response = MagicMock()
        mock_spelling_response.status_code = 200
        mock_spelling_response.json.return_value = {"suggestionGroup": {}}

        with patch.object(client, "get") as mock_get:
            mock_get.side_effect = [
                mock_rxcui_response,
                mock_approx_response,
                mock_spelling_response,
            ]

            result = await client.get_all_drug_data("nonexistent_xyz")

        assert result["found"] is False

    async def test_get_all_drug_data_with_rxcui_hint(self, client: RxNormClient) -> None:
        mock_info_response = MagicMock()
        mock_info_response.status_code = 200
        mock_info_response.json.return_value = {"properties": {"rxcui": "1191"}}

        mock_related_response = MagicMock()
        mock_related_response.status_code = 200
        mock_related_response.json.return_value = {"allRelatedGroup": {"conceptGroup": []}}

        mock_ndc_response = MagicMock()
        mock_ndc_response.status_code = 200
        mock_ndc_response.json.return_value = {"ndcGroup": {}}

        mock_interactions_response = MagicMock()
        mock_interactions_response.status_code = 200
        mock_interactions_response.json.return_value = {}

        with patch.object(client, "get") as mock_get:
            mock_get.side_effect = [
                mock_info_response,
                mock_related_response,
                mock_ndc_response,
                mock_interactions_response,
            ]

            result = await client.get_all_drug_data("aspirin", rxcui_hint="1191")

        assert result["found"] is True
        assert result["rxcui"] == "1191"
