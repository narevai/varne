from datetime import UTC, datetime

from pydantic import TypeAdapter

from varne.providers.jsonplaceholder.types import JsonPlaceholderPost
from varne.providers.types import RowRaw, RowStaging


def transform_posts(row: RowRaw) -> list[RowStaging]:
    now = datetime.now(UTC)
    rows_staging: list[RowStaging] = []
    adapter = TypeAdapter(list[JsonPlaceholderPost])
    posts_typed = adapter.validate_json(row.payload)
    for post in posts_typed:
        row_staging: RowStaging = RowStaging(
            stack_id=row.stack_id,
            source_id=row.source_id,
            provider=row.provider,
            id="jsonplaceholder",
            event_time=now,
            amount=float(len(post.body)),
        )
        rows_staging.append(row_staging)

    return rows_staging
