"""Local file system storage adapter."""

import asyncio
from pathlib import Path

from app.infrastructure.audio_storage.port import AudioStoragePort


class LocalStorageAdapter(AudioStoragePort):

    def __init__(self, base_path: Path):
        self._base_path = base_path
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, data: bytes, filename: str) -> str:
        file_path = self._base_path / filename
        await asyncio.to_thread(file_path.write_bytes, data)
        return str(file_path)