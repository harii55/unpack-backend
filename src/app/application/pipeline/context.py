"""Pipeline execution context. Shared state for a single pipeline run."""

from dataclasses import dataclass, field

from app.domain.pronunciations.models import PronunciationEntry


@dataclass
class PipelineContext:
    """
    Data bag that travels through all pipeline steps.
    
    Loaded once by the orchestrator at pipeline start.
    Term Extraction reads pronunciation_dict keys to skip known terms.
    Orchestrator merges new terms after Term Extraction.
    TTS Preparation consumes the full merged dictionary.
    """

    # written_form (lowercase) -> spoken_form mapping
    pronunciation_dict: dict[str, str] = field(default_factory=dict)

    # Subset of pronunciation_dict keys that are admin-verified.
    # TTS Preparation trusts these unconditionally.
    verified_terms: set[str] = field(default_factory=set)

    @staticmethod
    def from_entries(entries: list[PronunciationEntry]) -> "PipelineContext":
        """Build context from DB entries. Called once per pipeline run."""
        return PipelineContext(
            pronunciation_dict={
                e.written_form.lower(): e.spoken_form for e in entries
            },
            verified_terms={
                e.written_form.lower() for e in entries if e.is_verified
            },
        )

    def merge_new_terms(self, terms: list[dict[str, str]]) -> None:
        """
        Add newly extracted terms into the in-memory dictionary.
        Called by the orchestrator after Term Extraction + bulk_upsert.
        Uses First-In Wins: Never overwrites existing terms (verified OR unverified)
        to keep memory perfectly synced with the database state.
        """
        for term in terms:
            key = term["written_form"].lower()
            
            if key not in self.pronunciation_dict:
                self.pronunciation_dict[key] = term["spoken_form"]