from datetime import UTC, datetime

from varne.analytics.usage import get_source_meta
from varne.config import SourceId, SourceType, StackId
from varne.db.schema import TableName
from varne.db.types import DatabaseBackend


def test_get_usage_by_id(db: DatabaseBackend):
    now = datetime.now(UTC)

    stack_id: StackId = "stack_test"
    source_id: SourceId = "source_test"

    db.insert(
        TableName.DIM_SOURCE_META,
        [
            {
                "stack_id": stack_id,
                "source_id": source_id,
                "extracted_at": now,
                "value_name": "id",
                "value": SourceType.JSONPLACEHOLDER,
            },
            {
                "stack_id": stack_id,
                "source_id": source_id,
                "extracted_at": now,
                "value_name": "amount",
                "value": str(12.0),
            },
            {
                "stack_id": stack_id,
                "source_id": source_id,
                "extracted_at": now,
                "value_name": "id",
                "value": SourceType.JSONPLACEHOLDER,
            },
            {
                "stack_id": stack_id,
                "source_id": source_id,
                "extracted_at": now,
                "value_name": "amount",
                "value": str(8.0),
            },
        ],
    )

    result = get_source_meta(db, stack_id).execute()

    assert len(result) == 1
    assert result.iloc[0]["total_amount"] == 20.0
