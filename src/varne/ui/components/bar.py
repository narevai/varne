from decimal import Decimal
from typing import NamedTuple

from nicegui import ui

from varne.ui.components.tip import TIP_PROPS, Tip, tip_table


class Segment(NamedTuple):
    """One part of a bar: what it is worth, what it says, and what it is."""

    amount: Decimal
    kind: str
    # What is said of it when it is hovered or tapped, as the rows of a table: the name
    # of a field and its value, the way the tooltips of the charts say it.
    tip: Tip
    # Written on it when there is room: the logo, else the text, else the symbol that
    # stands in for a logo.
    text: str = ""
    logo: str = ""
    # A logo drawn in black only, to be shown light on the dark theme.
    mono: bool = False
    placeholder: str = ""


def bar(segments: list[Segment], scale: Decimal, ordered: bool = False) -> None:
    """One bar, on a scale that it shares with the other.

    What is written on a segment is shown where it fits, see theme.py. On an ordered
    bar it stops at the first segment where it does not fit: no segment to its right
    is written on.
    """
    with ui.element("div").classes("bar bar-ordered" if ordered else "bar"):
        for segment in segments:
            if segment.amount <= 0 or scale <= 0:
                continue

            width = f"{float(segment.amount / scale * 100):.2f}%"
            with (
                ui.element("div")
                .classes(f"bar-seg {segment.kind}")
                .style(f"width: {width}")
            ):
                if segment.logo or segment.text or segment.placeholder:
                    with ui.element("div").classes("seg-text"):
                        if segment.logo:
                            ui.element("img").props(f"src={segment.logo}").classes(
                                "seg-logo logo-mono" if segment.mono else "seg-logo"
                            )
                        elif segment.text:
                            ui.label(segment.text)
                        else:
                            ui.icon(segment.placeholder, size="24px").classes(
                                "opacity-40"
                            )
                # a mouse hovers over it, a finger taps it and the tip stays until the next tap
                with ui.tooltip().classes("seg-tip").props(TIP_PROPS):
                    tip_table(segment.tip)
                with (
                    ui.menu()
                    .classes("seg-menu")
                    .props(f"anchor='top middle' self='bottom middle' {TIP_PROPS}")
                ):
                    tip_table(segment.tip)
