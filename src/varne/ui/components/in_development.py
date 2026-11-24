from datetime import datetime, timedelta

import pandas as pd
from nicegui import ui

from varne.config import SUPPORTED_SOURCES, SourceType
from varne.ui.components.bar_chart import bar_chart
from varne.ui.components.config_form import new_source, source_form

DAYS = 21
START = datetime(2026, 11, 1)


def sample(series: dict[str, float], y: str, name: str) -> pd.DataFrame:
    """A made-up month of data, shaped like what a source stores."""
    rows = [
        {"day": START + timedelta(days=day), name: label, y: base * (1 + day % 5 / 10)}
        for day in range(DAYS)
        for label, base in series.items()
    ]
    return pd.DataFrame(rows)


def in_development() -> None:
    """What the sources that are not offered yet look like, with made-up data."""
    ui.label("In development").classes("text-xl font-semibold")
    ui.label(
        "These sources work from the configuration file, but the app does not offer them yet. Their form and charts live here until they do."
    ).classes("text-sm opacity-70")

    with ui.card().classes("w-full"):
        ui.label("Source forms").classes("text-sm opacity-70")
        for source_type in SourceType:
            if source_type not in SUPPORTED_SOURCES:
                source_form(new_source(source_type), lambda: None)

    billing = sample(
        {"Pro": 1.5, "Build minutes": 0.6, "Bandwidth": 0.3}, "cost", "service"
    )
    usage = sample({"visitors": 120, "pageviews": 340}, "usage", "name")
    per_visitor = sample({"Cost per visitor": 0.01}, "cost", "series")

    with ui.card().classes("w-full"):
        bar_chart(
            "Billing (USD)",
            billing,
            x="day",
            y="cost",
            series="service",
            value_format=".2~r",
        )
        bar_chart(
            "Usage (visitors, pageviews)", usage, x="day", y="usage", series="name"
        )
        bar_chart(
            "Cost per visitor (USD)",
            per_visitor,
            x="day",
            y="cost",
            series="series",
            value_format=".2~r",
        )
