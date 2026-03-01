from litestar import Litestar
from litestar_granian import GranianPlugin

from app.domain.system.controllers import SystemController

# This is the ASGI application instance Granian will look for
app = Litestar(
    route_handlers=[SystemController],
    plugins=[GranianPlugin()],
    debug=True,
)
