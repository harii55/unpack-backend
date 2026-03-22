"""
Shared types and enums for Unpack.

Defines the shared vocabulary and state machine rules used across the entire application.
"""
from enum import StrEnum

class PipelineStatus(StrEnum):
    """
    Current state of a blog in the database.
    
    Flow: DRAFT → TERMS_EXTRACTED → ANALYZED → BLUEPRINTED → SCRIPTED
          → REVIEWED_(PASS|REVISE|FAIL) → TTS_READY → AUDIO_GENERATED → PUBLISHED
    """
    DRAFT = "draft"
    TERMS_EXTRACTED = "terms_extracted"
    ANALYZED = "analyzed"
    BLUEPRINTED = "blueprinted"
    SCRIPTED = "scripted"
    REVIEWED_PASS = "reviewed_pass"
    REVIEWED_REVISE = "reviewed_revise"
    REVIEWED_FAIL = "reviewed_fail"
    TTS_READY = "tts_ready"
    AUDIO_GENERATED = "audio_generated"
    PUBLISHED = "published"


class PipelineStep(StrEnum):
    """Processing steps the orchestrator executes."""
    TERM_EXTRACTION = "term_extraction"
    ANALYSIS = "analysis"
    BLUEPRINT = "blueprint"
    SCRIPT_GENERATION = "script_generation"
    QUALITY_GATE = "quality_gate"
    TTS_PREPARATION = "tts_preparation"
    AUDIO_GENERATION = "audio_generation"


class FormatType(StrEnum):
    """Audio narration style."""
    FIRST_PERSON = "first_person"
    DIALOGUE = "dialogue"


# Execution order for the orchestrator.
PIPELINE_STEP_ORDER: list[PipelineStep] = [
    PipelineStep.TERM_EXTRACTION,
    PipelineStep.ANALYSIS,
    PipelineStep.BLUEPRINT,
    PipelineStep.SCRIPT_GENERATION,
    PipelineStep.QUALITY_GATE,
    PipelineStep.TTS_PREPARATION,
    PipelineStep.AUDIO_GENERATION,
]

# Maps each step to its possible output statuses.
# Most steps have one outcome; quality_gate branches into three.
STEP_OUTCOMES: dict[PipelineStep, list[PipelineStatus]] = {
    PipelineStep.TERM_EXTRACTION: [PipelineStatus.TERMS_EXTRACTED],
    PipelineStep.ANALYSIS: [PipelineStatus.ANALYZED],
    PipelineStep.BLUEPRINT: [PipelineStatus.BLUEPRINTED],
    PipelineStep.SCRIPT_GENERATION: [PipelineStatus.SCRIPTED],
    PipelineStep.QUALITY_GATE: [
        PipelineStatus.REVIEWED_PASS,
        PipelineStatus.REVIEWED_REVISE,
        PipelineStatus.REVIEWED_FAIL,
    ],
    PipelineStep.TTS_PREPARATION: [PipelineStatus.TTS_READY],
    PipelineStep.AUDIO_GENERATION: [PipelineStatus.AUDIO_GENERATED],
}

# Allowed forward transitions. Prevents jumping from DRAFT to PUBLISHED.
# REVIEWED_REVISE and REVIEWED_FAIL are dead-ends; admin must manually re-run.
_FORWARD_TRANSITIONS: dict[PipelineStatus, list[PipelineStatus]] = {
    PipelineStatus.DRAFT: [PipelineStatus.TERMS_EXTRACTED],
    PipelineStatus.TERMS_EXTRACTED: [PipelineStatus.ANALYZED],
    PipelineStatus.ANALYZED: [PipelineStatus.BLUEPRINTED],
    PipelineStatus.BLUEPRINTED: [PipelineStatus.SCRIPTED],
    PipelineStatus.SCRIPTED: [
        PipelineStatus.REVIEWED_PASS,
        PipelineStatus.REVIEWED_REVISE,
        PipelineStatus.REVIEWED_FAIL,
    ],
    PipelineStatus.REVIEWED_PASS: [PipelineStatus.TTS_READY],
    PipelineStatus.TTS_READY: [PipelineStatus.AUDIO_GENERATED],
    PipelineStatus.AUDIO_GENERATED: [PipelineStatus.PUBLISHED],
    PipelineStatus.PUBLISHED: [PipelineStatus.AUDIO_GENERATED],  # unpublish
}

# Progression rank. Used to block invalid re-runs.
# Example: A blog at ANALYZED (rank 2) can't re-run SCRIPT_GENERATION (rank 4).
_STATUS_RANK: dict[PipelineStatus, int] = {
    PipelineStatus.DRAFT: 0,
    PipelineStatus.TERMS_EXTRACTED: 1,
    PipelineStatus.ANALYZED: 2,
    PipelineStatus.BLUEPRINTED: 3,
    PipelineStatus.SCRIPTED: 4,
    PipelineStatus.REVIEWED_PASS: 5,
    PipelineStatus.REVIEWED_REVISE: 5,
    PipelineStatus.REVIEWED_FAIL: 5,
    PipelineStatus.TTS_READY: 6,
    PipelineStatus.AUDIO_GENERATED: 7,
    PipelineStatus.PUBLISHED: 8,
}


def can_transition(current: PipelineStatus, target: PipelineStatus) -> bool:
    """Returns True if moving from current to target is allowed."""
    return target in _FORWARD_TRANSITIONS.get(current, [])


def can_rerun_from(current_status: PipelineStatus, step: PipelineStep) -> bool:
    """
    Returns True if the blog has progressed far enough to re-run this step.
    
    Example: A blog at REVIEWED_FAIL (rank 5) can re-run BLUEPRINT (rank 3),
    but a blog at ANALYZED (rank 2) cannot re-run SCRIPT_GENERATION (rank 4).
    """
    current_rank = _STATUS_RANK[current_status]
    step_min_rank = min(_STATUS_RANK[s] for s in STEP_OUTCOMES[step])
    return current_rank >= step_min_rank


def get_step_index(step: PipelineStep) -> int:
    """Returns the position of this step in PIPELINE_STEP_ORDER."""
    return PIPELINE_STEP_ORDER.index(step)


def get_steps_after(step: PipelineStep) -> list[PipelineStep]:
    """Returns all steps that come after this one. Used to invalidate stale artifacts."""
    idx = get_step_index(step)
    return PIPELINE_STEP_ORDER[idx + 1:]

def get_rollback_status(step: PipelineStep) -> PipelineStatus:
    rollback_map = {
        PipelineStep.TERM_EXTRACTION: PipelineStatus.DRAFT,
        PipelineStep.ANALYSIS: PipelineStatus.TERMS_EXTRACTED,
        PipelineStep.BLUEPRINT: PipelineStatus.ANALYZED,
        PipelineStep.SCRIPT_GENERATION: PipelineStatus.BLUEPRINTED,
        PipelineStep.QUALITY_GATE: PipelineStatus.SCRIPTED,
        PipelineStep.TTS_PREPARATION: PipelineStatus.REVIEWED_PASS,
        PipelineStep.AUDIO_GENERATION: PipelineStatus.TTS_READY,
    }
    return rollback_map[step]
