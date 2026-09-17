from pydantic import TypeAdapter

from varne.config import SourceType
from varne.providers.jsonplaceholder.types import JsonPlaceholderPost
from varne.providers.types import RowDimSourceMeta, RowRaw


def post_to_row(row_raw: RowRaw, value_name: str, value: str) -> RowDimSourceMeta:
    row_staging: RowDimSourceMeta = RowDimSourceMeta(
        stack_id=row_raw.stack_id,
        source_id=row_raw.source_id,
        source_type=row_raw.source_type,
        extracted_at=row_raw.extracted_at,
        value_name=value_name,
        value=value,
    )

    return row_staging


def transform_posts(row: RowRaw) -> list[RowDimSourceMeta]:
    rows_staging: list[RowDimSourceMeta] = []
    adapter = TypeAdapter(list[JsonPlaceholderPost])
    posts_typed = adapter.validate_json(row.payload)
    for post in posts_typed:
        row_id: RowDimSourceMeta = post_to_row(
            row, value_name="id", value=str(SourceType.JSONPLACEHOLDER)
        )
        row_amount: RowDimSourceMeta = post_to_row(
            row, value_name="amount", value=str(len(post.body))
        )
        rows_staging.append(row_id)
        rows_staging.append(row_amount)

    return rows_staging
