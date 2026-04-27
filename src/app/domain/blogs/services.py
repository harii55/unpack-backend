"""Blog CQRS services."""

from datetime import datetime, timezone
from uuid import UUID

from app.common.types import (
    PipelineStatus,
    PipelineStep,
    can_rerun_from,
    can_transition,
    get_steps_after,
    get_rollback_status,
)
from app.domain.blogs.models import Blog, BlogArtifact
from app.domain.blogs.repositories import BlogArtifactRepository, BlogRepository
from app.exceptions import InvalidStateTransitionError


# Queries (Reads)
class BlogQueryService:

    def __init__(self, blog_repo: BlogRepository, artifact_repo: BlogArtifactRepository):
        self._blog_repo = blog_repo
        self._artifact_repo = artifact_repo

    async def get_blog(self, blog_id: UUID) -> Blog:
        return await self._blog_repo.get(blog_id)

    async def get_blog_with_artifacts(self, blog_id: UUID) -> Blog:
        return await self._blog_repo.get_with_artifacts(blog_id)

    async def list_by_topic(self, topic_id: UUID) -> list[Blog]:
        return await self._blog_repo.list_by_topic(topic_id)

    async def get_current_artifact(self, blog_id: UUID, step: PipelineStep) -> BlogArtifact | None:
        return await self._artifact_repo.get_current(blog_id, step)

    async def list_published_by_topic(self, topic_id: UUID) -> list[Blog]:
        """Return all published blogs in a topic, ordered by sequence position."""
        return await self._blog_repo.list_published_by_topic(topic_id)


# Commands (Writes)
class BlogCommandService:

    def __init__(self, blog_repo: BlogRepository, artifact_repo: BlogArtifactRepository):
        self._blog_repo = blog_repo
        self._artifact_repo = artifact_repo

    async def create_blog(
        self,
        topic_id: UUID,
        title: str,
        source_text: str,
        source_url: str | None = None,
        sequence_position: int = 0,
        generate_until_step: PipelineStep = PipelineStep.AUDIO_GENERATION,
    ) -> Blog:
        blog = Blog(
            topic_id=topic_id,
            title=title,
            source_text=source_text,
            source_url=source_url,
            sequence_position=sequence_position,
            generate_until_step=generate_until_step,
        )
        self._blog_repo.add(blog)
        return blog

    async def transition_status(self, blog_id: UUID, target: PipelineStatus) -> Blog:
        """Validates and applies a forward state transition."""
        blog = await self._blog_repo.get(blog_id)

        if not can_transition(blog.pipeline_status, target):
            raise InvalidStateTransitionError(blog.pipeline_status, target)

        blog.pipeline_status = target
        return blog

    async def prepare_rerun(self, blog_id: UUID, step: PipelineStep) -> Blog:
        """
        Validates a re-run is allowed, invalidates downstream artifacts,
        and cleanly resets the state machine.
        """
        blog = await self._blog_repo.get(blog_id)

        if not can_rerun_from(blog.pipeline_status, step):
            raise InvalidStateTransitionError(blog.pipeline_status, step)

        # Invalidate this step + everything downstream
        steps_to_invalidate = [step] + get_steps_after(step)
        await self._artifact_repo.mark_stale(blog_id, steps_to_invalidate)

        # Reset status to the state exactly preceding this step
        blog.pipeline_status = get_rollback_status(step)
        return blog

    async def save_artifact(self, blog_id: UUID, step: PipelineStep, content: str) -> BlogArtifact:
        return await self._artifact_repo.save(blog_id, step, content)

    async def publish(self, blog_id: UUID) -> Blog:
        blog = await self.transition_status(blog_id, PipelineStatus.PUBLISHED)
        blog.published_at = datetime.now(timezone.utc)
        return blog

    async def unpublish(self, blog_id: UUID) -> Blog:
        blog = await self.transition_status(blog_id, PipelineStatus.AUDIO_GENERATED)
        blog.published_at = None
        return blog

    async def set_audio_info(self, blog_id: UUID, file_path: str, duration_seconds: int) -> Blog:
        blog = await self._blog_repo.get(blog_id)
        blog.audio_file_path = file_path
        blog.audio_duration_seconds = duration_seconds
        return blog
    
    async def override_quality_gate(self, blog_id: UUID) -> Blog:
        """Admin force-passes a REVISE/FAIL verdict to continue the pipeline."""
        blog = await self._blog_repo.get(blog_id)

        if blog.pipeline_status not in (
            PipelineStatus.REVIEWED_REVISE,
            PipelineStatus.REVIEWED_FAIL,
        ):
            raise InvalidStateTransitionError(
                blog.pipeline_status, PipelineStatus.REVIEWED_PASS,
            )

        blog.pipeline_status = PipelineStatus.REVIEWED_PASS
        return blog