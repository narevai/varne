from datetime import UTC, datetime
from typing import cast

from varne.analytics.meta import get_source_meta
from varne.config import SourceId, SourceType, StackId
from varne.db.schema import TableName
from varne.db.types import DatabaseBackend


def test_get_source_meta(db: DatabaseBackend):
    now = datetime.now(UTC)

    stack_id: StackId = "stack_test"
    source_id: SourceId = "source_test"
    source_type: SourceType = SourceType.JSONPLACEHOLDER

    db.insert(
        TableName.DIM_SOURCE_META,
        [
            {
                "stack_id": stack_id,
                "source_id": source_id,
                "source_type": source_type,
                "extracted_at": now,
                "value_name": "id",
                "value": SourceType.JSONPLACEHOLDER,
            },
            {
                "stack_id": stack_id,
                "source_id": source_id,
                "source_type": source_type,
                "extracted_at": now,
                "value_name": "amount",
                "value": str(12.0),
            },
            {
                "stack_id": stack_id,
                "source_id": source_id,
                "source_type": source_type,
                "extracted_at": now,
                "value_name": "id",
                "value": SourceType.JSONPLACEHOLDER,
            },
            {
                "stack_id": stack_id,
                "source_id": source_id,
                "source_type": source_type,
                "extracted_at": now,
                "value_name": "amount",
                "value": str(8.0),
            },
        ],
    )

    result = get_source_meta(db, stack_id).to_pandas()

    assert result.shape[0] == 1
    assert result.shape[1] == 2
    result_dict = cast(dict[int, dict[str, str]], result.to_dict(orient="index"))

    assert result_dict[0].get("source_id") == source_id
    assert result_dict[0].get("source_type") == source_type
