"""Abstract interface for LLM text generation."""

from abc import ABC, abstractmethod


class LLMPort(ABC):

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Send a chat completion request. Returns the generated text."""
        ...