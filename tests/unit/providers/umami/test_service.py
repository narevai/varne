from datetime import UTC, datetime, timedelta
from typing import cast

import httpx2 as httpx
from pydantic import SecretStr

from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.umami.client import UmamiClient
from varne.providers.umami.service import UmamiService


def service(db: DatabaseBackend, seen: list[httpx.Request]) -> UmamiService:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body: dict[str, object] = {
            "pageviews": [{"x": "2026-11-01T00:00:00Z", "y": 12}],
            "sessions": [{"x": "2026-11-01T00:00:00Z", "y": 5}],
        }
        return httpx.Response(200, json=body, request=request)

    client = UmamiClient(
        httpx.Client(transport=httpx.MockTransport(handler)), SecretStr("key")
    )
    return UmamiService(
        db,
        client,
        stack_id="stack",
        source_id="source",
        website_ids=["w1", "w2"],
        lookback_days=9,
        now=lambda: datetime(2026, 9, 10, 12, tzinfo=UTC),
    )


def test_usage_is_fetched_for_every_website(db: DatabaseBackend):
    seen: list[httpx.Request] = []

    service(db, seen).fetch_source_data()

    assert [r.url.path for r in seen] == [
        "/v1/websites/w1/pageviews",
        "/v1/websites/w2/pageviews",
    ]
    assert seen[0].headers["authorization"] == "Bearer key"
    assert seen[0].url.params["unit"] == "day"
    assert seen[0].url.params["startAt"] == str(
        int(datetime(2026, 9, 1, tzinfo=UTC).timestamp() * 1000)
    )
    assert cast(int, db.table(TableName.RAW).count().execute()) == 2
    assert cast(int, db.table(TableName.FACT_USAGE).count().execute()) == 4


def test_sync_checks_every_website_and_stores_its_id(db: DatabaseBackend):
    seen: list[httpx.Request] = []

    service(db, seen).fetch_source_meta()

    assert [r.url.path for r in seen] == [
        "/v1/websites/w1/pageviews",
        "/v1/websites/w2/pageviews",
    ]
    assert cast(int, db.table(TableName.DIM_SOURCE_META).count().execute()) == 2


def test_all_websites_of_one_pull_share_extracted_at(db: DatabaseBackend):
    ticks = iter(
        datetime(2026, 9, 10, 12, tzinfo=UTC) + timedelta(seconds=i) for i in range(100)
    )

    def handler(request: httpx.Request) -> httpx.Response:
        body: dict[str, object] = {
            "pageviews": [{"x": "2026-09-01T00:00:00Z", "y": 1}],
            "sessions": [{"x": "2026-09-01T00:00:00Z", "y": 1}],
        }
        return httpx.Response(200, json=body, request=request)

    client = UmamiClient(
        httpx.Client(transport=httpx.MockTransport(handler)), SecretStr("k")
    )
    service = UmamiService(
        db, client, "stack", "source", ["w1", "w2", "w3"], now=lambda: next(ticks)
    )

    service.fetch_source_data()

    for table in (TableName.RAW, TableName.FACT_USAGE):
        stamps = db.table(table).extracted_at.nunique().execute()
        assert cast(int, stamps) == 1
