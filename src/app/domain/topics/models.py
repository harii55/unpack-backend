"""Topic model."""
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import BaseModel

if TYPE_CHECKING:
    from app.domain.blogs.models import Blog

class Topic(BaseModel):
    __tablename__ = "topics"
    
    name: Mapped[str] = mapped_column(String(255), unique=True)
    display_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=False)
    
    # Eager loading is left off to prevent N+1 queries.
    blogs: Mapped[list[Blog]] = relationship(
        back_populates="topic",
        order_by="Blog.sequence_position",
        cascade="all, delete-orphan",
    )