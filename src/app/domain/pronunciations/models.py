from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import BaseModel


class PronunciationEntry(BaseModel):
    __tablename__ = "pronunciation_entries"

    # We enforce lowercase at the application level to ensure 'gRPC' and 'grpc' don't conflict
    written_form: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    spoken_form: Mapped[str] = mapped_column(String(500))
    is_verified: Mapped[bool] = mapped_column(default=False)