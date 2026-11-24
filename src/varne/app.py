import asyncio
import sys
from pathlib import Path

from loguru import logger
from nicegui import app as nicegui_app
from nicegui import ui

from varne.api.v1 import router
from varne.cassettes import CassetteManager
from varne.demo import DEMO_CASSETTE
from varne.demo.seed import reset_demo, seed_demo
from varne.settings import get_settings
from varne.telemetry import track_server_start
from varne.ui import theme  # noqa: F401
from varne.ui.pages.dashboard import page_dashboard  # noqa: F401
from varne.ui.pages.gallery import page_gallery  # noqa: F401
from varne.ui.pages.integrations import page_integrations  # noqa: F401

settings = get_settings()

logger.remove()
logger.add(sys.stderr, level=settings.log_level)

app = nicegui_app
app.include_router(router, prefix="/api/v1")
cassette_manager = None
demo_cassettes: CassetteManager | None = None
background: asyncio.Task[None] | None = None


async def after_start() -> None:
    """What waits until the app is up, so that it never holds the start back."""
    global demo_cassettes

    # first, because the demo plays back every request that comes after it
    await track_server_start(settings)

    if settings.demo_mode:
        demo_cassettes = CassetteManager([DEMO_CASSETTE])
        demo_cassettes.start()
        try:
            await asyncio.to_thread(seed_demo)
        except Exception as exc:
            logger.error(f"Demo data could not be made: {exc}")


@app.on_startup
async def startup() -> None:
    global cassette_manager, background
    if settings.debug:
        from varne.dependencies import get_cassette_manager

        cassette_manager = get_cassette_manager()
        cassette_manager.start()

    if settings.demo_mode:
        logger.info("Demo mode: the sample stack, on a database of its own")
        reset_demo(Path(settings.config_path), Path(settings.database_path))

    background = asyncio.create_task(after_start())


@app.on_shutdown
def shutdown() -> None:
    global cassette_manager
    if background is not None:
        _ = background.cancel()
    if demo_cassettes is not None:
        demo_cassettes.stop()
    if cassette_manager is not None:
        cassette_manager.stop()


def main() -> None:
    try:
        ui.run(
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            show=False,
        )
    finally:
        if cassette_manager is not None:
            cassette_manager.stop()


if __name__ in {"__main__", "__mp_main__"}:
    main()
