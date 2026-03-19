"""SQLAlchemy-advAlchemy base model for Unpack."""

from advanced_alchemy.base import UUIDAuditBase


class BaseModel(UUIDAuditBase):
    """
    All domain models inherit from this.
    
    Provides: id (UUID), created_at, updated_at automatically.
    """
    __abstract__ = True