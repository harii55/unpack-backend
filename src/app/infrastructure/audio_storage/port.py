"""Abstract interface for file persistence."""

from abc import ABC, abstractmethod


class AudioStoragePort(ABC):

    @abstractmethod
    async def save(self, data: bytes, filename: str) -> str:
        """Persist binary data. Returns the storage reference."""
        ...