import ibis
from ibis.expr.types.relations import Table

from varne.config import SourceId, StackId
from varne.db.schema import TableFactBilling
from varne.db.types import DatabaseBackend


def get_source_billing(
    db: DatabaseBackend,
    stack_id: StackId,
    source_id: SourceId,
    page: int = 1,
    page_size: int = 25,
) -> Table:
    staging = db.table(TableFactBilling().name)

    offset = (page - 1) * page_size

    records = (
        staging.filter(staging.stack_id == stack_id, staging.source_id == source_id)
        .order_by(ibis.desc(staging.extracted_at))
        .limit(page_size, offset=offset)
    )

    return records


def get_billing_per_day(db: DatabaseBackend) -> Table:
    staging = db.table(TableFactBilling().name)

    records = (
        staging.group_by(
            day=ibis._.charge_period_start.truncate("D"),
            stack_id=ibis._.stack_id,
            source_id=ibis._.source_id,
            currency=ibis._.billing_currency,
        )
        .aggregate(cost=ibis._.billed_cost.sum())
        .order_by("day")
    )

    return records
