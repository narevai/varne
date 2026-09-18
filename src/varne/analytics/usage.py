import ibis
from ibis.expr.types.relations import Table

from varne.config import StackId
from varne.db.schema import TableDimSourceMeta
from varne.db.types import DatabaseBackend


def get_source_meta(db: DatabaseBackend, stack_id: StackId) -> Table:
    staging = db.table(TableDimSourceMeta().name)

    window = ibis.window(
      group_by=staging.source_id,
      order_by=ibis.desc(staging.extracted_at)
    )

    records = (
      staging
      .filter(staging.stack_id == stack_id)
      .mutate(row_number=ibis.row_number().over(window=window))
      .filter(lambda c: c.row_number == 1)  # pyright: ignore[reportArgumentType, reportUnknownLambdaType]
      .select(
        staging.source_id,
        staging.source_type
      )
    )

    return records
