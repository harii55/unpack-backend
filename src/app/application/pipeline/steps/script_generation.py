"""Script Generation step. Writes the full first-person audio narration."""

from app.application.pipeline.context import PipelineContext
from app.application.pipeline.prompts.script_generation import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.application.pipeline.steps.base import BaseLLMStep, StepResult
from app.common.types import PipelineStep


class ScriptGenerationStep(BaseLLMStep):

    @property
    def step_name(self) -> PipelineStep:
        return PipelineStep.SCRIPT_GENERATION

    def _temperature(self) -> float:
        return 0.7

    def _build_messages(
        self,
        source_text: str,
        artifacts: dict[PipelineStep, str],
        context: PipelineContext,
    ) -> list[dict[str, str]]:
        analysis = artifacts[PipelineStep.ANALYSIS]
        blueprint = artifacts[PipelineStep.BLUEPRINT]
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(
                source_text, analysis, blueprint,
            )},
        ]

    def _parse_response(self, raw: str) -> StepResult:
        return StepResult(content=raw.strip())