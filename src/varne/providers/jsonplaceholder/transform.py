from datetime import UTC, datetime

from pydantic import TypeAdapter

from varne.providers.jsonplaceholder.types import JsonPlaceholderPost
from varne.providers.types import RowStaging


def transform_posts(posts: str) -> list[RowStaging]:
    now = datetime.now(UTC)
    rows: list[RowStaging] = []
    adapter = TypeAdapter(list[JsonPlaceholderPost])
    posts_typed = adapter.validate_json(posts)
    for post in posts_typed:
        row = RowStaging(
            id="jsonplaceholder",
            event_time=now,
            amount=float(len(post.body)),
        )
        rows.append(row)

    return rows
