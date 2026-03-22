"""Blog and BlogArtifact repositories."""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.types import PipelineStep
from app.domain.blogs.models import Blog, BlogArtifact
from app.exceptions import EntityNotFoundError


class BlogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, blog_id: UUID) -> Blog:
        blog = await self.session.get(Blog, blog_id)
        if not blog:
            raise EntityNotFoundError("Blog", blog_id)
        return blog

    async def get_with_artifacts(self, blog_id: UUID) -> Blog:
        """Fetches a blog with all current artifacts eagerly loaded."""
        statement = (
            select(Blog)
            .where(Blog.id == blog_id)
            .options(selectinload(Blog.artifacts))
        )
        result = await self.session.execute(statement)
        blog = result.scalar_one_or_none()
        
        if not blog:
            raise EntityNotFoundError("Blog", blog_id)
        return blog

    async def list_by_topic(self, topic_id: UUID) -> list[Blog]:
        statement = (
            select(Blog)
            .where(Blog.topic_id == topic_id)
            .order_by(Blog.sequence_position)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    def add(self, blog: Blog) -> None:
        self.session.add(blog)


class BlogArtifactRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_current(self, blog_id: UUID, step: PipelineStep) -> BlogArtifact | None:
        """Returns the current artifact for a given blog and step, or None."""
        statement = (
            select(BlogArtifact)
            .where(
                BlogArtifact.blog_id == blog_id,
                BlogArtifact.step_name == step,
                BlogArtifact.is_current.is_(True),
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def _get_latest_version(self, blog_id: UUID, step: PipelineStep) -> int:
        """Internal helper: Returns the highest version number, or 0 if none exist."""
        statement = (
            select(BlogArtifact.version)
            .where(
                BlogArtifact.blog_id == blog_id,
                BlogArtifact.step_name == step,
            )
            .order_by(BlogArtifact.version.desc())
            .limit(1)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none() or 0

    async def mark_stale(self, blog_id: UUID, steps: list[PipelineStep]) -> None:
        """
        Bulk-stales artifacts. 
        Used internally before saving, and externally to invalidate downstream steps.
        """
        if not steps:
            return
            
        statement = (
            update(BlogArtifact)
            .where(
                BlogArtifact.blog_id == blog_id,
                BlogArtifact.step_name.in_(steps),
                BlogArtifact.is_current.is_(True),
            )
            .values(is_current=False)
        )
        await self.session.execute(statement)

    async def save(self, blog_id: UUID, step: PipelineStep, content: str) -> BlogArtifact:
        """Creates a new versioned artifact. Marks previous versions stale first."""
        # 1. Deprecate the old active version
        await self.mark_stale(blog_id, [step])
        
        # 2. Calculate the next version integer
        latest_version = await self._get_latest_version(blog_id, step)

        # 3. Save the new artifact
        artifact = BlogArtifact(
            blog_id=blog_id,
            step_name=step,
            version=latest_version + 1,
            content=content,
            is_current=True,
        )
        self.session.add(artifact)
        return artifact