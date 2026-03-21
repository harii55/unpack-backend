"""Analysis step. Deep structural breakdown of the source article."""

from app.application.pipeline.context import PipelineContext
from app.application.pipeline.prompts.analysis import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.application.pipeline.steps.base import BaseLLMStep, StepResult
from app.common.types import PipelineStep


class AnalysisStep(BaseLLMStep):

    @property
    def step_name(self) -> PipelineStep:
        return PipelineStep.ANALYSIS

    def _build_messages(
        self,
        source_text: str,
        artifacts: dict[PipelineStep, str],
        context: PipelineContext,
    ) -> list[dict[str, str]]:
        term_list = artifacts.get(PipelineStep.TERM_EXTRACTION, "[]")
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(source_text, term_list)},
        ]

    def _parse_response(self, raw: str) -> StepResult:
        return StepResult(content=raw.strip())