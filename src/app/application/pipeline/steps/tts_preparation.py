"""TTS Preparation step. Replaces terms with pronunciation-friendly forms."""

from app.application.pipeline.context import PipelineContext
from app.application.pipeline.prompts.tts_preparation import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.application.pipeline.steps.base import BaseLLMStep, StepResult
from app.common.types import PipelineStep


class TTSPreparationStep(BaseLLMStep):

    @property
    def step_name(self) -> PipelineStep:
        return PipelineStep.TTS_PREPARATION

    def _build_messages(
        self,
        source_text: str,
        artifacts: dict[PipelineStep, str],
        context: PipelineContext,
    ) -> list[dict[str, str]]:
        script = artifacts[PipelineStep.SCRIPT_GENERATION]
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(
                script,
                pronunciation_dict=context.pronunciation_dict,
                verified_terms=context.verified_terms,
            )},
        ]

    def _parse_response(self, raw: str) -> StepResult:
        return StepResult(content=raw.strip())