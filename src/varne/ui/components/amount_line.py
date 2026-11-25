from nicegui import ui


def amount_line(
    label: str,
    value: str,
    unit: str = "",
    *,
    apart: bool = False,
    strong: bool = False,
) -> None:
    """One line of the profitability: what it is, and what it comes to, on the right.

    A line that is `apart` has a little room above it, to set it off from those before.
    """
    with ui.row().classes(
        "w-full justify-between items-baseline" + (" figure-apart" if apart else "")
    ):
        ui.label(label).classes("text-sm font-semibold" if strong else "text-sm")
        with ui.row().classes("items-baseline gap-1"):
            ui.label(value).classes("statement-figure")
            if unit:
                ui.label(unit).classes("text-sm faint")
