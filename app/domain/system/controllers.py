from litestar import Controller, get


class SystemController(Controller):
    """Health endpoints for monitoring."""

    path = "/system"

    @get("/health")
    async def health_check(self) -> dict[str, str]:
        """Check health."""
        return {
            "status": "healthy",
            "message": "App is live!",
        }
