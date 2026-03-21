"""Pipeline orchestrator. Drives the FSM and executes steps in sequence."""

import json
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.pipeline.context import PipelineContext
from app.application.pipeline.steps.analysis import AnalysisStep
from app.application.pipeline.steps.audio_generation import AudioGenerationStep
from app.application.pipeline.steps.base import BasePipelineStep, StepResult
from app.application.pipeline.steps.blueprint import BlueprintStep
from app.application.pipeline.steps.quality_gate import QualityGateStep
from app.application.pipeline.steps.script_generation import ScriptGenerationStep
from app.application.pipeline.steps.term_extraction import TermExtractionStep
from app.application.pipeline.steps.tts_preparation import TTSPreparationStep
from app.common.types import (
    PIPELINE_STEP_ORDER,
    STEP_OUTCOMES,
    PipelineStatus,
    PipelineStep,
)
from app.domain.blogs.repositories import BlogArtifactRepository, BlogRepository
from app.domain.blogs.services import BlogCommandService, BlogQueryService
from app.domain.pronunciations.repositories import PronunciationRepository
from app.exceptions import PipelineStepError, QualityGateHaltError
from app.infrastructure.llm.port import LLMPort
from app.infrastructure.audio_storage.port import AudioStoragePort
from app.infrastructure.tts.port import TTSPort

logger = logging.getLogger(__name__)

_STATUS_TO_NEXT_INDEX: dict[PipelineStatus, int] = {
    PipelineStatus.DRAFT: 0,
    PipelineStatus.TERMS_EXTRACTED: 1,
    PipelineStatus.ANALYZED: 2,
    PipelineStatus.BLUEPRINTED: 3,
    PipelineStatus.SCRIPTED: 4,
    PipelineStatus.REVIEWED_PASS: 5,
    PipelineStatus.TTS_READY: 6,
}


class PipelineOrchestrator:

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        llm: LLMPort,
        tts: TTSPort,
        storage: AudioStoragePort,
    ):
        self._session_factory = session_factory
        self._tts = tts
        self._storage = storage

        self._llm_steps: dict[PipelineStep, BasePipelineStep] = {
            PipelineStep.TERM_EXTRACTION: TermExtractionStep(llm),
            PipelineStep.ANALYSIS: AnalysisStep(llm),
            PipelineStep.BLUEPRINT: BlueprintStep(llm),
            PipelineStep.SCRIPT_GENERATION: ScriptGenerationStep(llm),
            PipelineStep.QUALITY_GATE: QualityGateStep(llm),
            PipelineStep.TTS_PREPARATION: TTSPreparationStep(llm),
        }

    async def run(self, blog_id: UUID) -> None:
        """
        Execute the pipeline from the blog's current status
        through to its generate_until_step.

        Each step's DB work happens in its own short-lived session.
        LLM and TTS calls happen outside any session.
        """
        # Short session: load blog state and pronunciation dictionary
        async with self._session_factory() as session:
            blog_query = self._build_query_service(session)
            blog = await blog_query.get_blog_with_artifacts(blog_id)

            source_text = blog.source_text
            generate_until = blog.generate_until_step
            current_status = blog.pipeline_status

            artifacts: dict[PipelineStep, str] = {
                a.step_name: a.content
                for a in blog.artifacts
                if a.is_current
            }

            pronunciation_repo = PronunciationRepository(session)
            entries = await pronunciation_repo.get_all()
            context = PipelineContext.from_entries(entries)

        steps = self._get_steps_to_run(current_status, generate_until)
        if not steps:
            logger.info(
                "Blog %s: nothing to run (status=%s, until=%s)",
                blog_id, current_status, generate_until,
            )
            return

        logger.info("Blog %s: running steps %s", blog_id, [s.value for s in steps])

        for step_enum in steps:
            logger.info("Blog %s: executing %s", blog_id, step_enum)

            # No DB connection held during LLM/TTS calls
            step = self._get_step(step_enum, blog_id)
            try:
                result = await step.execute(source_text, artifacts, context)
            except Exception as exc:
                raise PipelineStepError(step_enum, blog_id, str(exc)) from exc

            # Short session: persist result and advance state
            async with self._session_factory() as session:
                blog_command = self._build_command_service(session)

                await blog_command.save_artifact(blog_id, step_enum, result.content)

                if step_enum == PipelineStep.TERM_EXTRACTION:
                    pronunciation_repo = PronunciationRepository(session)
                    terms = json.loads(result.content)
                    await pronunciation_repo.bulk_upsert(terms)
                    context.merge_new_terms(terms)

                if step_enum == PipelineStep.AUDIO_GENERATION:
                    await blog_command.set_audio_info(
                        blog_id, result.audio_file_path, result.audio_duration_seconds,
                    )

                status = self._resolve_status(step_enum, result)
                await blog_command.transition_status(blog_id, status)
                await session.commit()

            artifacts[step_enum] = result.content
            logger.info("Blog %s: %s → %s", blog_id, step_enum, status)

            if step_enum == PipelineStep.QUALITY_GATE and status != PipelineStatus.REVIEWED_PASS:
                raise QualityGateHaltError(blog_id, status, result.content)

    def _build_query_service(self, session: AsyncSession) -> BlogQueryService:
        return BlogQueryService(
            BlogRepository(session), BlogArtifactRepository(session),
        )

    def _build_command_service(self, session: AsyncSession) -> BlogCommandService:
        return BlogCommandService(
            BlogRepository(session), BlogArtifactRepository(session),
        )

    def _get_steps_to_run(
        self,
        current_status: PipelineStatus,
        until_step: PipelineStep,
    ) -> list[PipelineStep]:
        start_index = _STATUS_TO_NEXT_INDEX.get(current_status)
        if start_index is None:
            return []
        end_index = PIPELINE_STEP_ORDER.index(until_step) + 1
        return PIPELINE_STEP_ORDER[start_index:end_index]

    def _get_step(self, step: PipelineStep, blog_id: UUID) -> BasePipelineStep:
        if step == PipelineStep.AUDIO_GENERATION:
            return AudioGenerationStep(self._tts, self._storage, blog_id)
        return self._llm_steps[step]

    def _resolve_status(self, step: PipelineStep, result: StepResult) -> PipelineStatus:
        if step == PipelineStep.QUALITY_GATE and result.verdict:
            return result.verdict
        return STEP_OUTCOMES[step][0]