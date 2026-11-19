import ibis
from ibis.expr.types.relations import Table

from varne.analytics.latest import latest_per_day
from varne.config import SourceId, StackId
from varne.db.schema import TableFactUsage
from varne.db.types import DatabaseBackend


def get_source_usage(
    db: DatabaseBackend,
    stack_id: StackId,
    source_id: SourceId,
    page: int = 1,
    page_size: int = 25,
) -> Table:
    staging = db.table(TableFactUsage().name)

    offset = (page - 1) * page_size

    staging = staging.filter(
        staging.stack_id == stack_id, staging.source_id == source_id
    )

    records = (
        latest_per_day(staging, "event_time")
        .order_by(ibis.desc("event_time"))
        .limit(page_size, offset=offset)
    )

    return records
