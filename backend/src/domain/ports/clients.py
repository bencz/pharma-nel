"""
Client Interfaces (Ports).

Protocol classes defining contracts for external clients.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass(slots=True)
class LLMMessage:
    """Message in a conversation."""

    role: str
    content: str


@dataclass(slots=True)
class LLMToolCall:
    """Tool call from LLM response."""

    name: str
    arguments: dict[str, Any]
    id: str


@dataclass(slots=True)
class LLMResponse:
    """Response from LLM completion."""

    content: str
    model: str
    usage: dict[str, int]
    raw_response: Any = None
    tool_calls: list[LLMToolCall] | None = None


@dataclass(slots=True)
class LLMEmbeddingResponse:
    """Response from LLM embedding."""

    embedding: list[float]
    model: str
    usage: dict[str, int]


class ILLMClient(Protocol):
    """Interface for LLM clients."""

    @property
    def provider(self) -> LLMProvider:
        """Get the LLM provider type."""
        ...

    @property
    def model(self) -> str:
        """Get the current model name."""
        ...

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a completion."""
        ...

    async def complete_with_file(
        self,
        messages: list[LLMMessage],
        file_content: bytes,
        file_name: str,
        file_type: str = "application/pdf",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a completion with a file attachment."""
        ...

    async def get_embedding(self, text: str) -> LLMEmbeddingResponse:
        """Get embedding vector for text."""
        ...


class IFDAClient(Protocol):
    """Interface for FDA API client."""

    async def search_drugsfda(self, drug_name: str, limit: int = 100) -> list[dict[str, Any]]:
        ...

    async def search_labels(self, drug_name: str, limit: int = 100) -> list[dict[str, Any]]:
        ...

    async def get_all_drug_data(
        self,
        drug_name: str,
        include_events: bool = True,
        events_limit: int = 100,
    ) -> dict[str, list[dict[str, Any]]]:
        ...


class IRxNormClient(Protocol):
    """Interface for RxNorm API client."""

    async def get_rxcui_by_name(self, drug_name: str) -> list[dict[str, Any]]:
        ...

    async def get_drug_interactions(self, rxcui: str) -> list[dict[str, Any]]:
        ...

    async def get_all_drug_data(
        self,
        drug_name: str,
        rxcui_hint: str | None = None,
    ) -> dict[str, Any]:
        ...
