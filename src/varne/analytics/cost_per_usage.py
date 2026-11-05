import ibis
from ibis.expr.types.relations import Table

from varne.config import SourceId, StackId
from varne.db.schema import TableFactBilling, TableFactUsage
from varne.db.types import DatabaseBackend


def get_source_cost_per_usage(
    db: DatabaseBackend,
    stack_id: StackId,
    source_id: SourceId,
    usage_name: str = "visitors",
) -> Table:
    billing = db.table(TableFactBilling().name)
    usage = db.table(TableFactUsage().name)

    daily_cost = (
        billing.filter(billing.stack_id == stack_id, billing.source_id == source_id)
        .group_by(day=ibis._.charge_period_start.truncate("D"))
        .aggregate(cost=ibis._.billed_cost.sum())
    )

    daily_usage = (
        usage.filter(
            usage.stack_id == stack_id,
            usage.source_id == source_id,
            usage.usage_name == usage_name,
        )
        .group_by(day=ibis._.event_time.truncate("D"))
        .aggregate(units=ibis._.usage.sum())
    )

    records = (
        daily_cost.join(daily_usage, "day")
        .filter(ibis._.units > 0)
        .select(
            "day",
            cost_per_usage=ibis._.cost / ibis._.units,
            series=ibis.literal(usage_name),
        )
        .order_by("day")
    )

    return records
