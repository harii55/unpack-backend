"""Blueprint step. Plans the audio script section by section."""

from app.application.pipeline.context import PipelineContext
from app.application.pipeline.prompts.blueprint import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.application.pipeline.steps.base import BaseLLMStep, StepResult
from app.common.types import PipelineStep


class BlueprintStep(BaseLLMStep):

    @property
    def step_name(self) -> PipelineStep:
        return PipelineStep.BLUEPRINT

    def _build_messages(
        self,
        source_text: str,
        artifacts: dict[PipelineStep, str],
        context: PipelineContext,
    ) -> list[dict[str, str]]:
        analysis = artifacts[PipelineStep.ANALYSIS]
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(source_text, analysis)},
        ]

    def _parse_response(self, raw: str) -> StepResult:
        return StepResult(content=raw.strip())