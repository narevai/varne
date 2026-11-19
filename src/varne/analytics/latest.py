from typing import cast

import ibis
from ibis.expr.types.relations import Table
from ibis.expr.types.temporal import TimestampColumn


def latest_per_day(table: Table, time_column: str) -> Table:
    day = cast(TimestampColumn, table[time_column]).truncate("D")
    latest = table.extracted_at.max().over(
        ibis.window(group_by=[table.stack_id, table.source_id, day])
    )

    return table.filter(table.extracted_at == latest)
