"""What pops up when something is hovered, or tapped on a phone.

Every tip looks the same, see theme.css, and comes and goes the same way: no wait, then a
short fade. The tooltips of the charts are Vega's, and theme.css makes those match.
"""

from nicegui import ui

type Tip = tuple[tuple[str, str], ...]

# for a tooltip made in Python
TIP_PROPS = "delay=0 hide-delay=0 transition-show=fade transition-hide=fade transition-duration=120"
# for a `q-tooltip` in a template of a table
TIP_ATTRIBUTES = 'transition-show="fade" transition-hide="fade" :transition-duration="120" :delay="0" :hide-delay="0"'


def tip_table(rows: Tip) -> None:
    """The rows of a tip: the name of a field, and its value."""
    with ui.element("table").classes("tip-table"):
        for key, value in rows:
            with ui.element("tr"):
                with ui.element("td").classes("key"):
                    ui.label(key)
                with ui.element("td").classes("value"):
                    ui.label(value)


def tip(*rows: tuple[str, str]) -> None:
    """A tip for the element it is made in, saying a few rows."""
    with ui.tooltip().classes("seg-tip").props(TIP_PROPS):
        tip_table(rows)
