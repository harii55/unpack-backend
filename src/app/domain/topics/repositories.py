"""Topic repository."""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.topics.models import Topic
from app.exceptions import EntityNotFoundError

class TopicRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, topic_id: UUID) -> Topic:
        topic = await self.session.get(Topic, topic_id)
        if not topic:
            raise EntityNotFoundError("Topic", topic_id)
        return topic

    async def list_all(self) -> list[Topic]:
        statement = select(Topic).order_by(Topic.display_order)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    def add(self, topic: Topic) -> None:
        """Synchronous add. The Litestar plugin handles the actual commit."""
        self.session.add(topic)