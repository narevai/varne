from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import cast

import pandas as pd
from nicegui import run, ui

from varne.analytics.comparison import get_container_costs_per_day
from varne.catalog.comparison import application_of, image_of
from varne.config import SourceId, StackId
from varne.db.lock import serialized
from varne.db.types import DatabaseBackend
from varne.ui.components.bar_chart import bar_chart


def cost_per_application(
    costs: list[tuple[datetime, str, str, Decimal]],
) -> pd.DataFrame:
    """Daily cost of every application, from `(day, container, tags, cost)`.

    What no container used is its own series, `Idle`.
    """
    totals: dict[tuple[datetime, str], Decimal] = defaultdict(Decimal)

    for day, name, tags, cost in costs:
        totals[day, application_of(name, image_of(tags))] += cost

    return pd.DataFrame(
        {
            "day": [day for day, _ in totals],
            "application": [application for _, application in totals],
            "cost": [float(cost) for cost in totals.values()],
        }
    )


@serialized
def get_application_cost_rows(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> pd.DataFrame:
    df = get_container_costs_per_day(db, stack_id, source_id).to_pandas()

    return cost_per_application(
        list(
            zip(
                cast(list[datetime], df["day"].tolist()),
                cast(list[str], df["service_name"].tolist()),
                cast(list[str], df["tags"].tolist()),
                [
                    Decimal(str(cost))
                    for cost in cast(list[object], df["cost"].tolist())
                ],
                strict=True,
            )
        )
    )


async def application_costs(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> None:
    df = await run.io_bound(get_application_cost_rows, db, stack_id, source_id)

    if df.empty:
        ui.label("No cost data available")
        return

    bar_chart(
        "Cost per application (USD)",
        df,
        x="day",
        y="cost",
        series="application",
        value_format=".2~r",
    )
