"""Term Extraction step. Identifies technical terms and pronunciation guides."""

import json
import re

from app.application.pipeline.context import PipelineContext
from app.application.pipeline.prompts.term_extraction import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.application.pipeline.steps.base import BaseLLMStep, StepResult
from app.common.types import PipelineStep


class TermExtractionStep(BaseLLMStep):

    @property
    def step_name(self) -> PipelineStep:
        return PipelineStep.TERM_EXTRACTION

    def _temperature(self) -> float:
        return 0.0

    def _build_messages(
        self,
        source_text: str,
        artifacts: dict[PipelineStep, str],
        context: PipelineContext,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(
                source_text,
                known_terms=set(context.pronunciation_dict.keys()),
            )},
        ]

    def _parse_response(self, raw: str) -> StepResult:
        cleaned = self._extract_json(raw)
        # Validate structure before storing
        terms = json.loads(cleaned)
        if not isinstance(terms, list):
            raise ValueError("Term extraction did not return a JSON array")
        for term in terms:
            if "written_form" not in term or "spoken_form" not in term:
                raise ValueError(f"Malformed term entry: {term}")
        return StepResult(content=cleaned)

    def _extract_json(self, raw: str) -> str:
        """Handle LLMs wrapping JSON in markdown fences or prose."""
        # Try to find a JSON array in the response
        fence_match = re.search(r"```(?:json)?\s*(\[.*?])\s*```", raw, re.DOTALL)
        if fence_match:
            return fence_match.group(1)

        bracket_match = re.search(r"\[.*]", raw, re.DOTALL)
        if bracket_match:
            return bracket_match.group(0)

        # Last resort: maybe the entire response is valid JSON
        return raw.strip()