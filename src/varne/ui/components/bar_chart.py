from typing import cast

import altair as alt
import pandas as pd
from nicegui import ui

FONT = "Geist, ui-sans-serif, system-ui, sans-serif"
PALETTE = [
    "#10a37f",
    "#5188cd",
    "#9274c3",
    "#d6a23a",
    "#4fb3a9",
    "#b5689d",
    "#669649",
    "#0094bc",
    "#8c6d4f",
    "#cf5c5c",
]
MAX_SERIES = len(PALETTE)
OTHER = "Other"
OTHER_COLOR = "#9aa0a6"


def group_small_series(df: pd.DataFrame, y: str, series: str, top: int) -> pd.DataFrame:
    totals = cast(pd.Series, df.groupby(series)[y].sum()).sort_values(ascending=False)
    keep = cast(list[str], totals.head(top).index.tolist())
    return df.assign(**{series: df[series].where(df[series].isin(keep), OTHER)})


def bar_chart(
    title: str,
    df: pd.DataFrame,
    x: str,
    y: str,
    series: str,
    value_format: str | None = None,
    top: int = MAX_SERIES,
    time_unit: str = "yearmonthdate",
    time_format: str = "%b %d",
):
    df = df.assign(**{y: df[y].astype(float)})
    total = cast(float, df[y].sum())
    df = group_small_series(df, y, series, top)
    names = sorted(
        cast(list[str], df[series].unique().tolist()), key=lambda n: (n == OTHER, n)
    )
    colors = [
        OTHER_COLOR if n == OTHER else PALETTE[i % len(PALETTE)]
        for i, n in enumerate(names)
    ]
    fmt = value_format or alt.Undefined
    single_series = len(cast(list[str], df[series].unique().tolist())) == 1

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(
                f"{time_unit}({x}):O", title=None, axis=alt.Axis(format=time_format)
            ),
            y=alt.Y(
                f"sum({y}):Q",
                title=None,
                axis=alt.Axis(tickCount=5, format=fmt),
            ),
            color=alt.Color(
                f"{series}:N",
                title=None,
                scale=alt.Scale(domain=names, range=colors),
                legend=None if single_series else alt.Legend(),
            ),
            order=alt.Order(f"sum({y}):Q", sort="descending"),
            tooltip=[
                alt.Tooltip(f"{time_unit}({x}):T", title="Date"),
                alt.Tooltip(f"{series}:N", title="Series"),
                alt.Tooltip(f"sum({y}):Q", title="Total", format=fmt),
            ],
        )
        .properties(
            width="container",
            height=260,
            # the axes count in the width, or they stick out of the card, and only the width
            # is fitted, so the plot is as tall in every chart and their axes line up
            autosize=alt.AutoSizeParams(type="fit-x", contains="padding"),
        )
        .configure(background="transparent", font=FONT)
        .configure_view(stroke=None)
        .configure_axis(
            domain=False,
            ticks=False,
            grid=False,
            labelColor="currentColor",
            labelOpacity=0.65,
            labelFontSize=11,
            labelPadding=8,
        )
        .configure_axisX(grid=False, labelAngle=0, labelOverlap="greedy")
        .configure_legend(
            orient="bottom",
            symbolType="circle",
            labelColor="currentColor",
            labelFontSize=12,
            labelLimit=260,
            columns=4,
            symbolLimit=0,
            columnPadding=16,
            offset=16,
        )
        .configure_range(category=PALETTE)
        .configure_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    )

    with ui.column().classes("w-full gap-1 chart-block"):
        ui.label(title).classes("text-sm font-medium")
        with ui.row().classes("gap-1 text-sm"):
            ui.label("Total").classes("faint")
            ui.label(f"{total:,.2f}").classes("font-medium")
        widget = alt.JupyterChart(
            chart, embed_options={"renderer": "svg", "actions": False}
        )
        ui.altair(widget).classes("w-full")
