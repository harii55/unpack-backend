"""Topic CQRS services."""
from uuid import UUID

from app.domain.topics.models import Topic
from app.domain.topics.repositories import TopicRepository

# Queries (Reads)
class TopicQueryService:
    """Handles all read-only operations for topics."""
    
    def __init__(self, repository: TopicRepository):
        self.repository = repository

    async def get_topic(self, topic_id: UUID) -> Topic:
        return await self.repository.get(topic_id)

    async def list_all_topics(self) -> list[Topic]:
        return await self.repository.list_all()

    async def list_active_topics(self) -> list[Topic]:
        """Example of a specific business query."""
        topics = await self.repository.list_all()
        return [t for t in topics if t.is_active]


# Commands (Writes) 
class TopicCommandService:
    """Handles all state-mutating operations for topics."""
    
    def __init__(self, repository: TopicRepository):
        self.repository = repository

    async def create_topic(self, name: str, display_order: int = 0) -> Topic:
        topic = Topic(name=name, display_order=display_order)
        self.repository.add(topic)
        # We rely on the Litestar DB plugin to automatically commit at the end of the HTTP request.
        return topic

    async def update_topic(self, topic_id: UUID, name: str | None = None, is_active: bool | None = None) -> Topic:
        topic = await self.repository.get(topic_id)
        
        if name is not None:
            topic.name = name
        if is_active is not None:
            topic.is_active = is_active
            
        # The object is already attached to the session; modifying it tracks the changes.
        return topic