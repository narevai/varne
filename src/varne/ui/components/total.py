from decimal import Decimal

from nicegui import ui

from varne.ui.components.amount_line import amount_line
from varne.ui.format import dollars


def total(label: str, amount: Decimal, rows: list[tuple[str, Decimal]]) -> None:
    """The total of a bar, on a line of its own. Opened, it says what it is made of."""
    if not rows:
        amount_line(label, dollars(amount), "/ mo", strong=True)
        return

    with (
        ui.expansion()
        .classes("w-full total-expansion")
        .props("dense switch-toggle-side") as expansion
    ):
        with expansion.add_slot("header"):
            amount_line(label, dollars(amount), "/ mo")
        with ui.column().classes("total-items w-full gap-1 pb-2"):
            for name, value in rows:
                amount_line(name, dollars(value), "/ mo")
