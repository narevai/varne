from datetime import UTC, datetime

from varne.analytics.usage import get_usage_by_id
from varne.config import SourceId, StackId
from varne.db.types import DatabaseBackend


def test_get_usage_by_id(db: DatabaseBackend):
    now = datetime.now(UTC)

    stack_id: StackId = "stack_test"
    source_id: SourceId = "source_test"

    db.insert(
        "staging",
        [
            {
                "stack_id": stack_id,
                "source_id": source_id,
                "id": "jsonplaceholder",
                "event_time": now,
                "amount": 12.0,
            },
            {
                "stack_id": stack_id,
                "source_id": source_id,
                "id": "jsonplaceholder",
                "event_time": now,
                "amount": 8.0,
            },
        ],
    )

    result = get_usage_by_id(db, stack_id).execute()

    assert len(result) == 1
    assert result.iloc[0]["total_amount"] == 20.0
