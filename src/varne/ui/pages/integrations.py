from nicegui import ui

from varne.ui.layout import create_layout


@ui.page("/integrations")
def page_integrations() -> None:
    # TODO
    layout = create_layout()
    with layout:
        ui.html("<h1>Integrations</h1>")
        ui.label("Integrations will appear here once configured.")
