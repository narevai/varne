import sys

from loguru import logger
from nicegui import app as nicegui_app
from nicegui import ui

from varne.api.v1 import router
from varne.settings import get_settings
from varne.ui.pages.dashboard import page_dashboard  # noqa: F401
from varne.ui.pages.integrations import page_integrations  # noqa: F401
from varne.ui.pages.settings import page_settings  # noqa: F401

settings = get_settings()

logger.remove()
logger.add(sys.stderr, level=settings.log_level)

app = nicegui_app
app.include_router(router, prefix="/api/v1")


def main() -> None:
    ui.run(
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        show=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
