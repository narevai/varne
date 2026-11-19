from collections.abc import Iterable
from dataclasses import dataclass
from typing import cast

import pandas as pd
from nicegui import run, ui

from varne.analytics.usage import get_usage_by_metric
from varne.config import SourceId, StackId
from varne.db.lock import serialized
from varne.db.types import DatabaseBackend
from varne.ui.components.bar_chart import bar_chart

# Whole-machine figures are stored under this stand-in for a container name.
SYSTEM = "system"
ALL_CONTAINERS = "*"

GIB = 1024**3
METRICS: dict[str, tuple[str, float]] = {
    "cpu": ("CPU (%)", 100),
    "memory": ("Memory (GiB)", GIB),
    "disk": ("Disk (GiB)", GIB),
    "load": ("Load average", 100),
}


@dataclass(frozen=True)
class UsageName:
    system: str
    entity: str
    metric: str


def parse_usage_names(names: Iterable[str]) -> list[UsageName] | None:
    """`<system>/<entity>/<metric>` names, or None when any name has another shape."""
    parsed: list[UsageName] = []

    for name in names:
        parts = name.split("/")
        if len(parts) != 3 or not all(parts):
            return None

        parsed.append(UsageName(*parts))

    return parsed or None


def order_metrics(metrics: Iterable[str]) -> list[str]:
    known = list(METRICS)
    return sorted(set(metrics), key=lambda m: (known.index(m) if m in known else 99, m))


@serialized
def get_metric_rows(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId, metric: str
) -> pd.DataFrame:
    return get_usage_by_metric(db, stack_id, source_id, metric).to_pandas()


def select_series(
    df: pd.DataFrame, metric: str, container: str, several_systems: bool
) -> pd.DataFrame:
    parts = cast(pd.DataFrame, df["usage_name"].str.split("/", expand=True))
    system = cast(pd.Series, parts[0])
    entity = cast(pd.Series, parts[1])

    keep: pd.Series
    series: pd.Series

    if container == SYSTEM:
        keep = entity == SYSTEM
        series = system
    else:
        keep = entity != SYSTEM
        if container != ALL_CONTAINERS:
            keep = keep & (entity == container)
        series = system + "/" + entity if several_systems else entity

    _, divisor = METRICS.get(metric, (metric, 1))
    selected = pd.DataFrame(
        {
            "event_time": df["event_time"],
            "series": series,
            "usage": df["usage"].astype(float) / divisor,
        }
    )

    return cast(pd.DataFrame, selected[keep])


async def resource_usage(
    db: DatabaseBackend,
    stack_id: StackId,
    source_id: SourceId,
    names: list[UsageName],
) -> None:
    metrics = order_metrics(name.metric for name in names)
    several_systems = len({name.system for name in names}) > 1

    def container_options(metric: str) -> dict[str, str]:
        containers = sorted(
            {n.entity for n in names if n.metric == metric and n.entity != SYSTEM}
        )
        options = {SYSTEM: "System"}
        if containers:
            options[ALL_CONTAINERS] = "All containers (top 10 + Other)"
            options.update({c: c for c in containers})
        return options

    with ui.row().classes("w-full items-end gap-4"):
        metric_select = ui.select(
            {m: METRICS.get(m, (m, 1))[0] for m in metrics},
            label="resource",
            value=metrics[0],
        ).classes("min-w-48")
        container_select = ui.select(
            container_options(metrics[0]),
            label="container",
            value=SYSTEM,
            with_input=True,
        ).classes("min-w-96")

    @ui.refreshable
    async def chart() -> None:
        metric = cast(str, metric_select.value)
        container = cast(str, container_select.value)

        df = await run.io_bound(get_metric_rows, db, stack_id, source_id, metric)
        df = select_series(df, metric, container, several_systems)

        if df.empty:
            ui.label("No usage data available")
            return

        bar_chart(
            METRICS.get(metric, (metric, 1))[0],
            df,
            x="event_time",
            y="usage",
            series="series",
            value_format=".3~r",
            time_unit="yearmonthdatehours",
            time_format="%b %d %H:00",
        )

    def on_metric_change() -> None:
        options = container_options(cast(str, metric_select.value))
        container_select.set_options(options)
        container_select.set_value(SYSTEM)
        container_select.set_visibility(len(options) > 1)
        chart.refresh()

    metric_select.on_value_change(on_metric_change)
    container_select.on_value_change(chart.refresh)
    container_select.set_visibility(len(container_options(metrics[0])) > 1)

    await chart()
