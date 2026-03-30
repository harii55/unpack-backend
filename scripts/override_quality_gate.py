"""Force-pass a blog stuck at REVISE or FAIL."""

import argparse
import app.domain.topics.models  # Pre-load to avoid SQLAlchemy relationship lookup errors
import asyncio
import logging

from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings
from app.domain.blogs.repositories import BlogArtifactRepository, BlogRepository
from app.domain.blogs.services import BlogCommandService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blog-id", required=True, help="UUID of the stuck blog")
    args = parser.parse_args()

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        blog_command = BlogCommandService(
            BlogRepository(session), BlogArtifactRepository(session),
        )
        blog = await blog_command.override_quality_gate(UUID(args.blog_id))
        await session.commit()
        logger.info("Blog %s: forced to REVIEWED_PASS", blog.id)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())