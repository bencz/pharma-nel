"""
OpenAI API Client.

Supports:
- Chat completions (GPT-4o-mini, GPT-4o, GPT-4-turbo)
- File completions via Responses API (PDF support)
- Embeddings (text-embedding-3-small, text-embedding-3-large)
"""

import base64
import json
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI

from src.domain.ports.clients import (
    ILLMClient,
    LLMEmbeddingResponse,
    LLMMessage,
    LLMProvider,
    LLMResponse,
    LLMToolCall,
)
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class OpenAIClientConfig:
    """OpenAI client configuration."""

    api_key: str
    model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    max_tokens: int = 16000
    temperature: float = 0.1


class OpenAIClient(ILLMClient):
    """
    OpenAI implementation of LLMClient contract.

    Supports chat completions, file completions (PDF), and embeddings.
    """

    def __init__(self, config: OpenAIClientConfig) -> None:
        self._config = config
        self._client = AsyncOpenAI(api_key=config.api_key)

        logger.info("openai_client_initialized", model=config.model)

    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OPENAI

    @property
    def model(self) -> str:
        return self._config.model

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a completion using OpenAI Chat API."""
        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        response = await self._client.chat.completions.create(
            model=self._config.model,
            messages=openai_messages,
            temperature=temperature if temperature is not None else self._config.temperature,
            max_tokens=max_tokens if max_tokens is not None else self._config.max_tokens,
        )

        usage = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        content = response.choices[0].message.content or ""

        logger.debug("openai_completion", tokens=usage["total_tokens"])

        return LLMResponse(
            content=content,
            model=response.model,
            usage=usage,
            raw_response=response,
        )

    async def complete_with_tools(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a completion with tool calling."""
        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        response = await self._client.chat.completions.create(
            model=self._config.model,
            messages=openai_messages,
            tools=tools,
            tool_choice="auto",
            temperature=temperature if temperature is not None else self._config.temperature,
            max_tokens=max_tokens if max_tokens is not None else self._config.max_tokens,
        )

        message = response.choices[0].message

        tool_calls: list[LLMToolCall] = []
        if message.tool_calls:
            for call in message.tool_calls:
                tool_calls.append(
                    LLMToolCall(
                        name=call.function.name,
                        arguments=json.loads(call.function.arguments),
                        id=call.id,
                    )
                )

        return LLMResponse(
            content=message.content or "",
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            raw_response=response,
            tool_calls=tool_calls or None,
        )

    async def complete_with_file(
        self,
        messages: list[LLMMessage],
        file_content: bytes,
        file_name: str,
        file_type: str = "application/pdf",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate a completion with a PDF file using OpenAI Responses API.

        Args:
            messages: List of messages in the conversation
            file_content: Raw file bytes
            file_name: Original filename
            file_type: MIME type of the file
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with generated content
        """
        file_base64 = base64.b64encode(file_content).decode("utf-8")

        input_messages: list[dict[str, Any]] = []
        for msg in messages:
            input_messages.append({
                "role": msg.role,
                "content": [{"type": "input_text", "text": msg.content}],
            })

        input_messages.append({
            "role": "user",
            "content": [
                {
                    "type": "input_file",
                    "filename": file_name,
                    "file_data": f"data:{file_type};base64,{file_base64}",
                },
            ],
        })

        logger.info(
            "openai_file_completion",
            filename=file_name,
            file_size=len(file_content),
        )

        response = await self._client.responses.create(
            model=self._config.model,
            input=input_messages,
            temperature=temperature if temperature is not None else self._config.temperature,
            max_output_tokens=max_tokens if max_tokens is not None else self._config.max_tokens,
        )

        content = response.output_text or ""

        usage = {
            "input_tokens": response.usage.input_tokens if response.usage else 0,
            "output_tokens": response.usage.output_tokens if response.usage else 0,
            "total_tokens": (
                (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
            ),
        }

        logger.info("openai_file_completion_done", tokens=usage["total_tokens"])

        return LLMResponse(
            content=content,
            model=self._config.model,
            usage=usage,
            raw_response=response,
        )

    async def get_embedding(self, text: str) -> LLMEmbeddingResponse:
        """Get embedding vector using OpenAI API."""
        response = await self._client.embeddings.create(
            model=self._config.embedding_model,
            input=text,
        )

        usage = {
            "input_tokens": response.usage.prompt_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        embedding = response.data[0].embedding

        logger.debug("openai_embedding", dimensions=len(embedding))

        return LLMEmbeddingResponse(
            embedding=embedding,
            model=response.model,
            usage=usage,
        )

    async def complete_json(
        self,
        messages: list[LLMMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate a completion and parse as JSON.

        Useful for structured extraction tasks.
        """
        response = await self.complete(messages, temperature, max_tokens)

        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        return json.loads(content.strip())
