"""Resume a pipeline from its current status."""

import argparse
import app.domain.topics.models  # Pre-load to avoid SQLAlchemy relationship lookup errors
import asyncio
import logging

from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.pipeline.orchestrator import PipelineOrchestrator
from app.config import get_settings
from app.infrastructure.llm.groq_adapter import GroqAdapter
from app.infrastructure.audio_storage.local_storage_adapter import LocalStorageAdapter
from app.infrastructure.tts.edge_tts_adapter import EdgeTTSAdapter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blog-id", required=True, help="UUID of the blog to resume")
    args = parser.parse_args()

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    orchestrator = PipelineOrchestrator(
        session_factory=session_factory,
        llm=GroqAdapter(api_key=settings.llm_api_key, model=settings.llm_model),
        tts=EdgeTTSAdapter(voice=settings.tts_voice),
        storage=LocalStorageAdapter(base_path=settings.audio_storage_path),
    )

    try:
        await orchestrator.run(UUID(args.blog_id))
        logger.info("Pipeline completed")
    except Exception as exc:
        logger.error("Pipeline halted: %s", exc)
        raise

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())