from datetime import UTC, datetime

from varne.analytics.usage import get_usage_by_id
from varne.db.types import DatabaseBackend


def test_get_usage_by_id(db: DatabaseBackend):
    now = datetime.now(UTC)

    db.insert(
        "staging",
        [
            {"id": "jsonplaceholder", "event_time": now, "amount": 12.0},
            {"id": "jsonplaceholder", "event_time": now, "amount": 8.0},
        ],
    )

    result = get_usage_by_id(db).execute()

    assert len(result) == 1
    assert result.iloc[0]["total_amount"] == 20.0
