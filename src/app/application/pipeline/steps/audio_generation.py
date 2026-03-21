"""Audio Generation step. Converts TTS-ready script to MP3 via edge-tts."""

from uuid import UUID

from app.application.pipeline.context import PipelineContext
from app.application.pipeline.steps.base import BasePipelineStep, StepResult
from app.common.types import PipelineStep
from app.infrastructure.audio_storage.port import AudioStoragePort
from app.infrastructure.tts.port import TTSPort


class AudioGenerationStep(BasePipelineStep):
    """
    Not an LLM step. Extends BasePipelineStep directly.
    Calls TTS for audio bytes, then Storage to persist them.
    """

    def __init__(self, tts: TTSPort, storage: AudioStoragePort, blog_id: UUID):
        self._tts = tts
        self._storage = storage
        self._blog_id = blog_id

    @property
    def step_name(self) -> PipelineStep:
        return PipelineStep.AUDIO_GENERATION

    async def execute(
        self,
        source_text: str,
        artifacts: dict[PipelineStep, str],
        context: PipelineContext,
    ) -> StepResult:
        tts_script = artifacts[PipelineStep.TTS_PREPARATION]

        audio_bytes = await self._tts.synthesize(tts_script)
        filename = f"{self._blog_id}.mp3"
        file_path = await self._storage.save(audio_bytes, filename)

        # Rough duration estimate: MP3 at 128kbps ≈ 16KB per second
        duration_seconds = len(audio_bytes) // 16_000

        return StepResult(
            content=f"Audio generated: {filename}",
            audio_file_path=file_path,
            audio_duration_seconds=duration_seconds,
        )