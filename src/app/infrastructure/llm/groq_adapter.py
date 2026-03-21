"""Groq LLM adapter using the groq Python SDK."""

import asyncio

from groq import (
    AsyncGroq,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)

from app.exceptions import LLMClientError
from app.infrastructure.llm.port import LLMPort

_MAX_RETRIES = 3


class GroqAdapter(LLMPort):

    def __init__(self, api_key: str, model: str):
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        kwargs: dict = {"model": self._model, "messages": messages}
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                response = await self._client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                if not content:
                    raise LLMClientError("Empty response from Groq")
                return content

            except (APITimeoutError, APIConnectionError, RateLimitError) as exc:
                last_error = exc
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)

            except APIStatusError as exc:
                # Non-retryable: auth errors, bad requests, etc.
                raise LLMClientError(
                    f"Groq API error {exc.status_code}: {exc.message}"
                ) from exc

        raise LLMClientError(
            f"Failed after {_MAX_RETRIES} retries: {last_error}"
        ) from last_error