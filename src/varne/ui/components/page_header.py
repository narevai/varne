from nicegui import ui


def page_header(title: str, subtitle: str = "") -> None:
    """The title of a page, with a line that says what the page is for."""
    with ui.column().classes("page-header"):
        ui.html(f"<h1>{title}</h1>")
        if subtitle:
            ui.label(subtitle).classes("page-subtitle")
