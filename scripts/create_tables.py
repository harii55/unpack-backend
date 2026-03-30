"""One-time table creation for local development."""

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings

# Import all models so SQLAlchemy registers them
from app.infrastructure.database.base import BaseModel
from app.domain.topics.models import Topic
from app.domain.blogs.models import Blog, BlogArtifact
from app.domain.pronunciations.models import PronunciationEntry


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    await engine.dispose()
    print("Tables created.")


if __name__ == "__main__":
    asyncio.run(main())