"""
Standalone script to test the full pipeline end-to-end.

Usage:
    python -m scripts.run_pipeline \
        --topic "System Design" \
        --title "Netflix Circuit Breakers" \
        --source path/to/article.txt

    OR pipe source text directly:

    cat article.txt | python -m scripts.run_pipeline \
        --topic "System Design" \
        --title "Netflix Circuit Breakers" \
        --stdin
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.pipeline.orchestrator import PipelineOrchestrator
from app.config import get_settings
from app.domain.blogs.models import Blog
from app.domain.blogs.repositories import BlogArtifactRepository, BlogRepository
from app.domain.blogs.services import BlogCommandService, BlogQueryService
from app.domain.topics.repositories import TopicRepository
from app.domain.topics.services import TopicCommandService, TopicQueryService
from app.infrastructure.llm.groq_adapter import GroqAdapter
from app.infrastructure.audio_storage.local_storage_adapter import LocalStorageAdapter
from app.infrastructure.tts.edge_tts_adapter import EdgeTTSAdapter
from app.domain.topics.models import Topic

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Unpack pipeline on an article.")
    parser.add_argument("--topic", required=True, help="Topic name (created if missing)")
    parser.add_argument("--title", required=True, help="Blog title")
    parser.add_argument("--source-url", default=None, help="Original article URL")

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--source", help="Path to a text file containing the article")
    source_group.add_argument("--stdin", action="store_true", help="Read article text from stdin")

    return parser.parse_args()


def read_source(args: argparse.Namespace) -> str:
    if args.stdin:
        text = sys.stdin.read().strip()
        if not text:
            raise SystemExit("Error: no text received from stdin")
        return text

    path = Path(args.source)
    if not path.exists():
        raise SystemExit(f"Error: file not found: {path}")
    return path.read_text().strip()


async def main() -> None:
    args = parse_args()
    source_text = read_source(args)
    settings = get_settings()

    logger.info("Source text: %d characters", len(source_text))

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    llm = GroqAdapter(api_key=settings.llm_api_key, model=settings.llm_model)
    tts = EdgeTTSAdapter(voice=settings.tts_voice)
    storage = LocalStorageAdapter(base_path=settings.audio_storage_path)

    # Short session: create topic and blog
    async with session_factory() as session:
        topic = await _find_or_create_topic(args.topic, session)
        blog = await _create_blog(
            session, topic.id, args.title, source_text, args.source_url,
        )
        await session.commit()
        blog_id = blog.id
        logger.info("Created blog %s", blog_id)

    # Pipeline manages its own sessions
    orchestrator = PipelineOrchestrator(
        session_factory=session_factory,
        llm=llm,
        tts=tts,
        storage=storage,
    )

    try:
        await orchestrator.run(blog_id)
        logger.info("Pipeline completed for blog %s", blog_id)
    except Exception as exc:
        logger.error("Pipeline halted: %s", exc)
        raise

    # Short session: load final state for summary
    async with session_factory() as session:
        blog_query = BlogQueryService(
            BlogRepository(session), BlogArtifactRepository(session),
        )
        blog = await blog_query.get_blog_with_artifacts(blog_id)
        _print_summary(blog)

    await engine.dispose()


async def _find_or_create_topic(name: str, session) -> "Topic":

    topic_repo = TopicRepository(session)
    topic_query = TopicQueryService(topic_repo)
    topics = await topic_query.list_all_topics()

    for topic in topics:
        if topic.name.lower() == name.lower():
            logger.info("Found existing topic: %s", topic.id)
            return topic

    topic_command = TopicCommandService(topic_repo)
    topic = await topic_command.create_topic(name=name)
    await session.flush() # Force ID generation before using it for the blog
    logger.info("Created new topic: %s (%s)", name, topic.id)
    return topic


async def _create_blog(session, topic_id, title, source_text, source_url) -> "Blog":
    blog_command = BlogCommandService(
        BlogRepository(session), BlogArtifactRepository(session),
    )
    return await blog_command.create_blog(
        topic_id=topic_id,
        title=title,
        source_text=source_text,
        source_url=source_url,
    )


def _print_summary(blog: Blog) -> None:
    print("\n" + "=" * 60)
    print(f"Blog:     {blog.title}")
    print(f"ID:       {blog.id}")
    print(f"Status:   {blog.pipeline_status}")
    print(f"Audio:    {blog.audio_file_path or 'N/A'}")
    print(f"Duration: {blog.audio_duration_seconds or 'N/A'}s")
    print(f"\nArtifacts:")
    for artifact in blog.artifacts:
        if artifact.is_current:
            preview = artifact.content[:100].replace("\n", " ")
            print(f"  [{artifact.step_name}] v{artifact.version}: {preview}...")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())