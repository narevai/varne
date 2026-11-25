from decimal import Decimal
from typing import cast

import ibis
from ibis.expr.types.relations import Table

from varne.analytics.latest import latest_per_day
from varne.catalog.comparison import ContainerCost, image_of
from varne.config import SourceId, SourceType, StackId
from varne.db.lock import serialized
from varne.db.schema import TableFactBilling
from varne.db.types import DatabaseBackend


def get_container_costs(db: DatabaseBackend, stack_id: StackId) -> Table:
    """What every container of the stack's Docker sources cost, with its image."""
    staging = db.table(TableFactBilling().name)
    staging = staging.filter(
        staging.stack_id == stack_id,
        staging.source_type == SourceType.DOCKER.value,
    )

    return (
        latest_per_day(staging, "charge_period_start")
        .group_by("source_id", "service_name", "tags")
        .aggregate(
            cost=ibis._.billed_cost.sum(),
            hours=ibis._.consumed_quantity.sum(),
        )
        .order_by("source_id", "service_name")
    )


def get_container_costs_per_day(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> Table:
    """What every container of one Docker source cost on each day."""
    staging = db.table(TableFactBilling().name)
    staging = staging.filter(
        staging.stack_id == stack_id, staging.source_id == source_id
    )

    return (
        latest_per_day(staging, "charge_period_start")
        .group_by(
            day=ibis._.charge_period_start.truncate("D"),
            service_name=ibis._.service_name,
            tags=ibis._.tags,
        )
        .aggregate(cost=ibis._.billed_cost.sum())
        .order_by("day")
    )


@serialized
def get_container_cost_rows(
    db: DatabaseBackend, stack_id: StackId
) -> list[ContainerCost]:
    df = get_container_costs(db, stack_id).to_pandas()

    return [
        ContainerCost(
            source_id=source_id,
            name=name,
            image=image_of(tags),
            cost=Decimal(str(cost)),
            hours=Decimal(str(hours)),
        )
        for source_id, name, tags, cost, hours in zip(
            cast(list[str], df["source_id"].tolist()),
            cast(list[str], df["service_name"].tolist()),
            cast(list[str], df["tags"].tolist()),
            cast(list[object], df["cost"].tolist()),
            cast(list[object], df["hours"].tolist()),
            strict=True,
        )
    ]
