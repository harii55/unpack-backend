"""Pipeline step base classes using Template Method pattern."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.application.pipeline.context import PipelineContext
from app.common.types import PipelineStatus, PipelineStep
from app.infrastructure.llm.port import LLMPort


@dataclass
class StepResult:
    """Output from any pipeline step."""
    content: str

    verdict: PipelineStatus | None = None

    audio_file_path: str | None = None
    audio_duration_seconds: int | None = None


class BasePipelineStep(ABC):
    """
    Common interface the orchestrator calls.
    All steps — LLM-based and audio — implement this.
    """

    @property
    @abstractmethod
    def step_name(self) -> PipelineStep: ...

    @abstractmethod
    async def execute(
        self,
        source_text: str,
        artifacts: dict[PipelineStep, str],
        context: PipelineContext,
    ) -> StepResult: ...


class BaseLLMStep(BasePipelineStep):
    """
    Template Method for the 6 LLM-based steps.

    Skeleton: build messages → call LLM → parse response.
    Subclasses fill in the specifics via _build_messages and _parse_response.
    """

    def __init__(self, llm: LLMPort):
        self._llm = llm

    async def execute(
        self,
        source_text: str,
        artifacts: dict[PipelineStep, str],
        context: PipelineContext,
    ) -> StepResult:
        messages = self._build_messages(source_text, artifacts, context)
        raw = await self._llm.generate(
            messages,
            temperature=self._temperature(),
            max_tokens=self._max_tokens(),
        )
        return self._parse_response(raw)

    @abstractmethod
    def _build_messages(
        self,
        source_text: str,
        artifacts: dict[PipelineStep, str],
        context: PipelineContext,
    ) -> list[dict[str, str]]: ...

    @abstractmethod
    def _parse_response(self, raw: str) -> StepResult:
        """Parse raw LLM output and construct the full result."""
        ...

    def _temperature(self) -> float | None:
        """Override per step. None lets the adapter use its default."""
        return None

    def _max_tokens(self) -> int | None:
        """Override per step. None lets the adapter use its default."""
        return None