"""Topic HTTP controllers."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from litestar import Controller, get
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.blogs.repositories import BlogArtifactRepository, BlogRepository
from app.domain.blogs.services import BlogQueryService
from app.domain.topics.repositories import TopicRepository
from app.domain.topics.services import TopicQueryService


@dataclass
class TopicResponse:
    """Public representation of a topic."""

    id: UUID
    name: str
    display_order: int


@dataclass
class BlogSummaryResponse:
    """Public representation of a published blog listing item."""

    id: UUID
    title: str
    sequence_position: int
    audio_duration_seconds: int | None
    published_at: datetime | None


class TopicController(Controller):
    """Topic endpoints."""

    path = "/topics"

    @get("/")
    async def list_topics(self, session: AsyncSession) -> list[TopicResponse]:
        """List all active topics."""
        svc = TopicQueryService(TopicRepository(session))
        topics = await svc.list_active_topics()
        return [
            TopicResponse(id=t.id, name=t.name, display_order=t.display_order)
            for t in topics
        ]

    @get("/{topic_id:uuid}/blogs")
    async def list_published_blogs(
        self,
        topic_id: UUID,
        session: AsyncSession,
    ) -> list[BlogSummaryResponse]:
        """List published blogs in a topic, ordered by sequence position."""
        svc = BlogQueryService(
            BlogRepository(session),
            BlogArtifactRepository(session),
        )
        blogs = await svc.list_published_by_topic(topic_id)
        return [
            BlogSummaryResponse(
                id=b.id,
                title=b.title,
                sequence_position=b.sequence_position,
                audio_duration_seconds=b.audio_duration_seconds,
                published_at=b.published_at,
            )
            for b in blogs
        ]
