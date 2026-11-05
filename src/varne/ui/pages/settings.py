from nicegui import ui

from varne.ui.layout import create_layout


@ui.page("/settings")
def page_settings() -> None:
    # TODO
    layout = create_layout()
    with layout:
        ui.html("<h1>Settings</h1>")
        ui.label("Settings will appear here once configured.")
