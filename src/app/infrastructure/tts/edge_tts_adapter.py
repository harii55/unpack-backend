"""Edge-TTS adapter using the edge-tts library."""

import asyncio

import edge_tts

from app.exceptions import TTSClientError
from app.infrastructure.tts.port import TTSPort

_MAX_RETRIES = 3


class EdgeTTSAdapter(TTSPort):

    def __init__(self, voice: str):
        self._voice = voice

    async def synthesize(self, text: str) -> bytes:
        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                communicate = edge_tts.Communicate(text, self._voice)
                chunks: list[bytes] = []

                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        chunks.append(chunk["data"])

                if not chunks:
                    raise RuntimeError("Empty audio stream, likely a dropped connection")

                return b"".join(chunks)

            except Exception as exc:
                last_error = exc
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)

        raise TTSClientError(
            f"Failed after {_MAX_RETRIES} retries: {last_error}"
        ) from last_error