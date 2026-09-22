import json
from datetime import UTC, datetime

from varne.config import SourceId, SourceType, StackId
from varne.providers.jsonplaceholder.transform import transform_meta
from varne.providers.types import RowDimSourceMeta, RowRaw


def test_transform_posts():
    stack_id: StackId = "stack_test"
    source_id: SourceId = "source_test"
    source_type = SourceType.JSONPLACEHOLDER
    now = datetime.now(UTC)
    url = "http://example.com"
    method = "GET"

    post = [
        {
            "id": 123,
            "userId": 7,
            "title": "Hello",
            "body": "abcdef",
        }
    ]

    post_str = json.dumps(post)

    post_row = RowRaw(
        stack_id=stack_id,
        source_id=source_id,
        source_type=source_type,
        method=method,
        url=url,
        extracted_at=now,
        payload=post_str,
    )

    rows = transform_meta(post_row)

    assert len(rows) == 2
    assert all(isinstance(row, RowDimSourceMeta) for row in rows)

    row_id = next(x for x in rows if x.value_name == "id")

    assert row_id.stack_id == stack_id
    assert row_id.source_id == source_id
    assert row_id.value == source_type

    row_amount = next(x for x in rows if x.value_name == "amount")
    assert row_amount.value == str(len("abcdef"))
