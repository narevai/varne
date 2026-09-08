from ibis.expr.types.relations import Table

from varne.db.schema import TableStaging
from varne.db.types import DatabaseBackend


def get_usage_by_id(db: DatabaseBackend) -> Table:
    staging = db.table(TableStaging().name)

    records = staging.group_by("id").aggregate(total_amount=staging.amount.sum())  # pyright: ignore[reportUnknownArgumentType, reportAttributeAccessIssue]

    return records
