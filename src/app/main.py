from collections.abc import AsyncGenerator

from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.datastructures import State
from litestar.di import Provide
from litestar_granian import GranianPlugin
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.domain.blogs.controllers import BlogController
from app.domain.system.controllers import SystemController
from app.domain.topics.controllers import TopicController


async def provide_db_session(state: State) -> AsyncGenerator[AsyncSession, None]:
    """Yield a scoped AsyncSession per request."""
    async with state.session_factory() as session:
        yield session


async def on_startup(app: Litestar) -> None:
    """Create the async engine and session factory on startup."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def on_shutdown(app: Litestar) -> None:
    """Dispose the engine connection pool on shutdown."""
    await app.state.engine.dispose()


app = Litestar(
    route_handlers=[SystemController, TopicController, BlogController],
    dependencies={"session": Provide(provide_db_session)},
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
    cors_config=CORSConfig(allow_origins=["*"]),
    plugins=[GranianPlugin()],
    debug=True,
)
