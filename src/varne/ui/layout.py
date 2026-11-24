from loguru import logger
from nicegui import context, ui
from nicegui.elements.column import Column

from varne.dependencies import get_config_manager
from varne.settings import get_settings
from varne.ui import theme  # noqa: F401
from varne.ui.components.nav_item import nav_item

DOCS_URL = "https://www.narev.ai/docs/varne/v1/index"


def create_layout(title: str = "") -> Column:
    dark = ui.dark_mode(True)
    config_manager = get_config_manager()
    if config_manager.error is not None:
        message = f"Configuration failed to load {config_manager.error} from file {config_manager.path.resolve()}"
        ui.notify(
            message=message,
            type="negative",
            timeout=0,
            close_button=True,
        )
        logger.error(message)

    with ui.left_drawer(top_corner=True, bottom_corner=True, value=True).props(
        "breakpoint=768 width=232"
    ) as drawer:
        with ui.row().classes("brand"):
            ui.label("V").classes("brand-mark")
            ui.label("Varne").classes("brand-name")

        nav_item("Dashboard", "space_dashboard", "/")
        nav_item("Integrations", "sync_alt", "/integrations")
        nav_item("Documentation", "menu_book", DOCS_URL, external=True)

        if get_settings().environment == "development":
            nav_item("Components", "widgets", "/dev/components")

        # the bottom of the menu is left free, Varne Cloud adds its account there
        ui.space()
        ui.label(f"v{get_settings().api_version}").classes("nav-version")

    with ui.header().classes("app-header"):
        ui.button(icon="menu_open", on_click=lambda: drawer.toggle()).props(
            "flat dense round"
        )
        ui.label(title).classes("header-title")
        ui.space()
        ui.button(icon="contrast", on_click=lambda: dark.toggle()).props(
            "flat dense round"
        ).tooltip("Switch theme")

    with context.client.layout:
        with ui.page_scroller(position="bottom-right", x_offset=20, y_offset=20):
            ui.button("Scroll to Top")

    content = ui.column()

    return content
