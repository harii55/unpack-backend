"""Quality Gate step. Reviews script against source for faithfulness."""

import re

from app.application.pipeline.context import PipelineContext
from app.application.pipeline.prompts.quality_gate import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.application.pipeline.steps.base import BaseLLMStep, StepResult
from app.common.types import PipelineStatus, PipelineStep

_VERDICT_MAP: dict[str, PipelineStatus] = {
    "PASS": PipelineStatus.REVIEWED_PASS,
    "REVISE": PipelineStatus.REVIEWED_REVISE,
    "FAIL": PipelineStatus.REVIEWED_FAIL,
}


class QualityGateStep(BaseLLMStep):

    @property
    def step_name(self) -> PipelineStep:
        return PipelineStep.QUALITY_GATE

    def _temperature(self) -> float:
        return 0.0

    def _build_messages(
        self,
        source_text: str,
        artifacts: dict[PipelineStep, str],
        context: PipelineContext,
    ) -> list[dict[str, str]]:
        script = artifacts[PipelineStep.SCRIPT_GENERATION]
        blueprint = artifacts[PipelineStep.BLUEPRINT]

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(source_text, blueprint, script)},
        ]

    def _parse_response(self, raw: str) -> StepResult:
        verdict_status = self._extract_verdict(raw)
        return StepResult(content=raw.strip(), verdict=verdict_status)

    def _extract_verdict(self, raw: str) -> PipelineStatus:
        match = re.search(r"VERDICT:\s*(PASS|REVISE|FAIL)", raw, re.IGNORECASE)
        if not match:
            # If we can't parse the verdict, treat it as a failure to be safe
            return PipelineStatus.REVIEWED_FAIL
        return _VERDICT_MAP[match.group(1).upper()]