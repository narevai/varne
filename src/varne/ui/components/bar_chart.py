from typing import cast

import altair as alt
import pandas as pd
from nicegui import ui

FONT = "Geist, ui-sans-serif, system-ui, sans-serif"
PALETTE = [
    "#5188cd",
    "#b5689d",
    "#669649",
    "#9274c3",
    "#0094bc",
    "#3f9b65",
    "#d6a23a",
    "#cf5c5c",
    "#4fb3a9",
    "#8c6d4f",
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
):
    df = df.assign(**{y: df[y].astype(float)})
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
            x=alt.X(f"yearmonthdate({x}):O", title=None, axis=alt.Axis(format="%b %d")),
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
            tooltip=[
                alt.Tooltip(f"yearmonthdate({x}):T", title="Date"),
                alt.Tooltip(f"{series}:N", title="Series"),
                alt.Tooltip(f"sum({y}):Q", title="Total", format=fmt),
            ],
        )
        .properties(width="container", height=260)
        .configure(background="transparent", font=FONT)
        .configure_view(stroke=None)
        .configure_axis(
            domain=False,
            ticks=False,
            gridColor="currentColor",
            gridOpacity=0.1,
            labelColor="currentColor",
            labelOpacity=0.65,
            labelFontSize=11,
            labelPadding=8,
        )
        .configure_axisX(grid=False, labelAngle=0)
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

    with ui.column().classes("w-full mt-6"):
        ui.label(title).classes("text-sm font-medium")
        widget = alt.JupyterChart(
            chart, embed_options={"renderer": "svg", "actions": False}
        )
        ui.altair(widget).classes("w-full")
