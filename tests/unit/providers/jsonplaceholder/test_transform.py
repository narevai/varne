import json
from datetime import UTC, datetime

from varne.config import SourceId, SourceType, StackId
from varne.providers.jsonplaceholder.transform import transform_posts
from varne.providers.types import RowRaw


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

    rows = transform_posts(post_row)

    assert len(rows) == 1

    row = rows[0]

    assert row.stack_id == stack_id
    assert row.source_id == source_id
    assert row.id == source_type
    assert row.amount == len("abcdef")
