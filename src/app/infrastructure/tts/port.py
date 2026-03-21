"""Abstract interface for text-to-speech generation."""

from abc import ABC, abstractmethod


class TTSPort(ABC):

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Convert text to audio. Returns raw audio bytes."""
        ...