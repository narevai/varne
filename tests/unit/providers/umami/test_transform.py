import json
from datetime import UTC, datetime

from varne.config import SourceType
from varne.providers.types import RowRaw
from varne.providers.umami.transform import transform_pageviews


def raw(payload: dict[str, object]) -> RowRaw:
    return RowRaw(
        stack_id="stack",
        source_id="source",
        source_type=SourceType.UMAMI,
        extracted_at=datetime(2026, 11, 18, tzinfo=UTC),
        method="GET",
        url="https://api.umami.is/v1/websites/w",
        payload=json.dumps(payload),
    )


def test_pageviews_and_sessions_become_usage_rows():
    rows = transform_pageviews(
        raw(
            {
                "pageviews": [{"x": "2026-11-01T00:00:00Z", "y": 12}],
                "sessions": [{"x": "2026-11-01T00:00:00Z", "y": 5}],
            }
        )
    )

    assert [(r.usage_name, r.usage) for r in rows] == [
        ("pageviews", 12),
        ("sessions", 5),
    ]
    assert rows[0].event_time == datetime(2026, 11, 1, tzinfo=UTC)


def test_empty_report_gives_no_rows():
    assert transform_pageviews(raw({"pageviews": [], "sessions": []})) == []
