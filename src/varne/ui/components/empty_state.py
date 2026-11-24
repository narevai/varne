from nicegui import ui

from varne.ui.layout import DOCS_URL


def empty_state(icon: str, title: str, text: str, action: str, target: str) -> None:
    """What a page says when there is nothing to show yet, and where to go from there."""
    with ui.column().classes("w-full items-center gap-2 py-16 text-center"):
        ui.icon(icon, size="56px").classes("opacity-40")
        ui.label(title).classes("text-xl")
        ui.label(text).classes("opacity-70 max-w-md")
        with ui.row().classes("mt-2 items-center"):
            ui.button(action, on_click=lambda: ui.navigate.to(target))
            ui.button(
                "Read the documentation",
                icon="menu_book",
                on_click=lambda: ui.navigate.to(DOCS_URL, new_tab=True),
            ).props("flat")


def no_stacks() -> None:
    empty_state(
        "layers",
        "No stacks yet",
        "A stack groups the sources of one product, such as its hosting, its AI providers and its analytics. Add one on the Integrations page to see its costs here.",
        "Open Integrations",
        "/integrations",
    )


def no_sources() -> None:
    empty_state(
        "extension",
        "This stack has no sources",
        "Add a source on the Integrations page, then sync it.",
        "Open Integrations",
        "/integrations",
    )
