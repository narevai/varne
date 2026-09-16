from pydantic import TypeAdapter

from varne.config import SourceType
from varne.providers.jsonplaceholder.types import JsonPlaceholderPost
from varne.providers.types import RowRaw, RowStaging


def transform_posts(row: RowRaw) -> list[RowStaging]:
    rows_staging: list[RowStaging] = []
    adapter = TypeAdapter(list[JsonPlaceholderPost])
    posts_typed = adapter.validate_json(row.payload)
    for post in posts_typed:
        row_staging: RowStaging = RowStaging(
            stack_id=row.stack_id,
            source_id=row.source_id,
            source_type=SourceType.JSONPLACEHOLDER,
            extracted_at=row.extracted_at,
            value_name="amount",
            value=str(len(post.body)),
        )
        rows_staging.append(row_staging)

    return rows_staging
