import ibis.expr.datatypes as dt
from ibis.expr.types.relations import Table

from varne.config import StackId
from varne.db.schema import TableDimSourceMeta
from varne.db.types import DatabaseBackend


def get_usage_by_id(db: DatabaseBackend, stack_id: StackId) -> Table:
    staging = db.table(TableDimSourceMeta().name)

    records = (
        staging.filter(staging.stack_id == stack_id, staging.value_name == "amount")
        .group_by(staging.source_id)
        .aggregate(total_amount=staging.value.cast('float64').sum())  # pyright: ignore[reportUnknownArgumentType, reportAttributeAccessIssue]
        .order_by(staging.source_id)
    )

    return records
