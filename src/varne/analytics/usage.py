from ibis.expr.types.relations import Table

from varne.config import StackId
from varne.db.schema import TableStaging
from varne.db.types import DatabaseBackend


def get_usage_by_id(db: DatabaseBackend, stack_id: StackId) -> Table:
    staging = db.table(TableStaging().name)

    records = (
        staging.filter(staging.stack_id == stack_id)
        .group_by("id")
        .aggregate(total_amount=staging.amount.sum())  # pyright: ignore[reportUnknownArgumentType, reportAttributeAccessIssue]
    )

    return records
