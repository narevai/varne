from collections.abc import Awaitable, Callable
from inspect import isawaitable

from nicegui import ui


def confirm(question: str, on_yes: Callable[[], Awaitable[None] | None]) -> None:
    async def yes() -> None:
        dialog.close()
        result = on_yes()
        if isawaitable(result):
            await result

    # the theme makes every card as wide as its parent, a dialog is not
    with ui.dialog() as dialog, ui.card().classes("!w-96 max-w-full"):
        ui.label(question)
        with ui.row():
            ui.button("Delete", on_click=yes).props("color=negative")
            ui.button("Cancel", on_click=dialog.close).props("flat")
    dialog.open()
