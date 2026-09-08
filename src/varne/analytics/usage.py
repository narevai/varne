import ibis
from ibis.expr.types.relations import Table

from varne.db.schema import TableStaging


def get_usage_by_id(db: ibis.BaseBackend) -> Table:
    staging = db.table(TableStaging().name)

    records = staging.group_by("id").aggregate(total_amount=staging.amount.sum())  # pyright: ignore[reportUnknownArgumentType, reportAttributeAccessIssue]

    return records
