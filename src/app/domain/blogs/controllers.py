"""Blog HTTP controllers."""

import asyncio
from pathlib import Path
from uuid import UUID

from litestar import Controller, Request, get
from litestar.exceptions import NotFoundException
from litestar.response import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.types import PipelineStatus
from app.domain.blogs.repositories import BlogRepository
from app.exceptions import EntityNotFoundError


def _read_file_range(path: Path, start: int, length: int) -> bytes:
    with open(path, "rb") as f:
        f.seek(start)
        return f.read(length)


def _read_full_file(path: Path) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _get_file_info(path: Path) -> tuple[bool, int]:
    """Return (exists, size) for a path without blocking the event loop."""
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return exists, size


class BlogController(Controller):
    """Blog endpoints."""

    path = "/blogs"

    @get("/{blog_id:uuid}/audio", media_type="audio/mpeg")
    async def stream_audio(
        self,
        blog_id: UUID,
        request: Request,
        session: AsyncSession,
    ) -> Response[bytes]:
        """Stream the MP3 audio for a published blog. Supports HTTP Range requests."""
        try:
            blog = await BlogRepository(session).get(blog_id)
        except EntityNotFoundError as exc:
            raise NotFoundException(detail=str(exc)) from exc

        if blog.pipeline_status != PipelineStatus.PUBLISHED:
            raise NotFoundException(detail=f"Blog {blog_id} is not published")

        if not blog.audio_file_path:
            raise NotFoundException(detail=f"No audio file for blog {blog_id}")

        file_path = Path(blog.audio_file_path)
        exists, file_size = await asyncio.to_thread(_get_file_info, file_path)
        if not exists:
            raise NotFoundException(detail="Audio file not found on server")

        range_header = request.headers.get("range", "")

        if range_header.startswith("bytes="):
            range_spec = range_header[6:]
            start_str, _, end_str = range_spec.partition("-")
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1

            data = await asyncio.to_thread(_read_file_range, file_path, start, length)
            return Response(
                content=data,
                status_code=206,
                media_type="audio/mpeg",
                headers={
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Accept-Ranges": "bytes",
                    "Content-Length": str(length),
                },
            )

        data = await asyncio.to_thread(_read_full_file, file_path)
        return Response(
            content=data,
            status_code=200,
            media_type="audio/mpeg",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            },
        )
