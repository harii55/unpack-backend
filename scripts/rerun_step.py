"""Rollback a blog to a specific step so it can be re-run."""

import argparse
import app.domain.topics.models  
import asyncio
import logging

from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.common.types import PipelineStep
from app.config import get_settings
from app.domain.blogs.repositories import BlogArtifactRepository, BlogRepository
from app.domain.blogs.services import BlogCommandService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blog-id", required=True, help="UUID of the blog")
    parser.add_argument(
        "--step", 
        type=PipelineStep, 
        choices=list(PipelineStep), 
        required=True, 
        help="The step you want to OVERWRITE/RE-RUN (e.g. script_generation)"
    )
    args = parser.parse_args()

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        blog_command = BlogCommandService(
            BlogRepository(session), BlogArtifactRepository(session),
        )
        blog = await blog_command.prepare_rerun(UUID(args.blog_id), args.step)
        await session.commit()
        logger.info(
            "Blog %s: Rolled back to %s. Ready to re-run %s.", 
            blog.id, blog.pipeline_status, args.step
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
