from collections.abc import Collection

import ibis
from ibis.expr.types.relations import Table

from varne.analytics.latest import latest_per_day
from varne.config import SourceId, StackId
from varne.db.schema import TableFactBilling
from varne.db.types import DatabaseBackend


def get_source_billing(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> Table:
    staging = db.table(TableFactBilling().name)
    staging = staging.filter(
        staging.stack_id == stack_id, staging.source_id == source_id
    )

    return (
        latest_per_day(staging, "charge_period_start")
        .group_by(
            charge_period_start=ibis._.charge_period_start.truncate("D"),
            service_name=ibis._.service_name,
            billing_currency=ibis._.billing_currency,
        )
        .aggregate(billed_cost=ibis._.billed_cost.sum())
        .filter(ibis._.billed_cost != 0)
        .order_by("charge_period_start")
    )


def get_billing_per_day(
    db: DatabaseBackend,
    stack_id: StackId | None = None,
    source_ids: Collection[SourceId] | None = None,
) -> Table:
    """Cost of every source per day, of the given sources only when they are given."""
    staging = db.table(TableFactBilling().name)

    if stack_id is not None:
        staging = staging.filter(staging.stack_id == stack_id)

    if source_ids is not None:
        staging = staging.filter(
            staging.source_id.isin(
                [ibis.literal(source_id) for source_id in source_ids]
            )
        )

    records = (
        latest_per_day(staging, "charge_period_start")
        .group_by(
            day=ibis._.charge_period_start.truncate("D"),
            stack_id=ibis._.stack_id,
            source_id=ibis._.source_id,
            currency=ibis._.billing_currency,
        )
        .aggregate(cost=ibis._.billed_cost.sum())
        .order_by("day")
    )

    return records
