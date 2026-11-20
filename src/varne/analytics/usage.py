from typing import cast

import ibis
from ibis.expr.types.relations import Table
from ibis.expr.types.strings import StringColumn

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


def get_usage_names(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> Table:
    staging = db.table(TableFactUsage().name)

    return (
        staging.filter(staging.stack_id == stack_id, staging.source_id == source_id)
        .select("usage_name")
        .distinct()
        .order_by("usage_name")
    )


def get_usage_by_metric(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId, metric: str
) -> Table:
    """Hourly rows of every `<system>/<entity>/<metric>` series of one source."""
    staging = db.table(TableFactUsage().name)
    staging = staging.filter(
        staging.stack_id == stack_id,
        staging.source_id == source_id,
        cast(StringColumn, staging.usage_name).endswith(f"/{metric}"),
    )

    return (
        latest_per_day(staging, "event_time")
        .select("event_time", "usage_name", "usage")
        .order_by("event_time")
    )
