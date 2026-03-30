"""System health and observability endpoints."""

from litestar import Controller, Response, get
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


class SystemController(Controller):
    """Health and metrics endpoints for monitoring."""

    path = "/system"

    @get("/health")
    async def health_check(self) -> dict[str, str]:
        """Check health."""
        return {
            "status": "healthy",
            "message": "App is live!",
        }

    @get("/metrics", media_type=CONTENT_TYPE_LATEST, sync_to_thread=False)
    def metrics(self) -> Response[bytes]:
        """Expose Prometheus metrics for scraping."""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )
