from datetime import UTC, datetime
from typing import cast

import httpx2 as httpx
from pydantic import SecretStr
from tests.unit.providers.anthropic.test_transform import page

from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.anthropic.client import AnthropicClient
from varne.providers.anthropic.service import AnthropicService


def test_service_follows_pages_and_stores_every_one(db: DatabaseBackend):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.params.get("page") is None:
            return httpx.Response(200, json=page("page_2", ["100"]), request=request)
        return httpx.Response(200, json=page(None, ["250"]), request=request)

    client = AnthropicClient(
        httpx.Client(transport=httpx.MockTransport(handler)), SecretStr("sk-ant-admin")
    )
    service = AnthropicService(
        db,
        client,
        stack_id="stack",
        source_id="source",
        lookback_days=9,
        now=lambda: datetime(2026, 9, 10, 12, tzinfo=UTC),
    )

    service.fetch_source_data()

    assert len(seen) == 2
    assert seen[0].headers["x-api-key"] == "sk-ant-admin"
    assert seen[0].url.params["starting_at"] == "2026-09-01T00:00:00+00:00"
    assert seen[0].url.params["ending_at"] == "2026-09-11T00:00:00+00:00"
    assert cast(int, db.table(TableName.RAW).count().execute()) == 2
    assert cast(int, db.table(TableName.FACT_BILLING).count().execute()) == 2


def test_sync_marks_the_source_as_connected(db: DatabaseBackend):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=page(None, []), request=request)

    client = AnthropicClient(
        httpx.Client(transport=httpx.MockTransport(handler)), SecretStr("x")
    )
    service = AnthropicService(db, client, stack_id="stack", source_id="source")

    service.fetch_source_meta()

    assert cast(int, db.table(TableName.DIM_SOURCE_META).count().execute()) == 1
