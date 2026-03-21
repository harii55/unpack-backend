"""
Application exceptions for Unpack.

Custom error hierarchy so the application can catch specific failures
without catching generic Python exceptions.
"""

from uuid import UUID

from app.common.types import PipelineStatus, PipelineStep


class UnpackError(Exception):
    """Base class for all application-specific exceptions."""
    pass


# Domain

class EntityNotFoundError(UnpackError):
    """Raised when a database lookup fails for a specific ID."""
    def __init__(self, entity_name: str, entity_id: UUID):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} {entity_id} not found")


class InvalidStateTransitionError(UnpackError):
    """Raised when a state change or re-run is not allowed from the current status."""
    def __init__(self, current: PipelineStatus, target: PipelineStatus | PipelineStep):
        self.current = current
        self.target = target
        if isinstance(target, PipelineStep):
            msg = f"Cannot re-run '{target}' from status '{current}'"
        else:
            msg = f"Cannot transition from '{current}' to '{target}'"
        super().__init__(msg)


# Pipeline 

class PipelineError(UnpackError):
    """Base class for all errors during pipeline execution."""
    pass


class PipelineStepError(PipelineError):
    """Raised when a specific step fails unexpectedly."""
    def __init__(self, step: PipelineStep, blog_id: UUID, detail: str):
        self.step = step
        self.blog_id = blog_id
        super().__init__(f"Step '{step}' failed for blog {blog_id}: {detail}")


class LLMClientError(PipelineError):
    """Raised when the LLM API call fails."""
    pass


class TTSClientError(PipelineError):
    """Raised when audio generation fails."""
    pass

class AudioStorageError(PipelineError):
    """Raised when writing audio bytes to disk or cloud storage fails."""
    pass

class QualityGateHaltError(PipelineError):
    """Raised when quality gate returns REVISE or FAIL. Pipeline halts for admin review."""
    def __init__(self, blog_id: UUID, verdict: PipelineStatus, issues: str):
        self.blog_id = blog_id
        self.verdict = verdict
        self.issues = issues
        super().__init__(f"Quality gate: {verdict} for blog {blog_id}")