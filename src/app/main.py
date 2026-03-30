"""Application entry point."""

from litestar import Litestar
from litestar_granian import GranianPlugin

from app.observability.controllers import SystemController
from app.observability.middleware import PrometheusMiddleware

app = Litestar(
    route_handlers=[SystemController],
    middleware=[PrometheusMiddleware],
    plugins=[GranianPlugin()],
    debug=True,
)
