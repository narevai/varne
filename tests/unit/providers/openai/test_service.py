from datetime import UTC, datetime
from typing import cast

import httpx2 as httpx
from pydantic import SecretStr

from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.openai.client import OpenAIClient
from varne.providers.openai.service import OpenAIService


def costs_page(next_page: str | None, value: float) -> dict[str, object]:
    return {
        "object": "page",
        "data": [
            {
                "object": "bucket",
                "start_time": 1730419200,
                "end_time": 1730505600,
                "results": [
                    {
                        "amount": {"value": value, "currency": "usd"},
                        "line_item": "gpt-5, input",
                        "project_id": "proj_1",
                    }
                ],
            }
        ],
        "has_more": next_page is not None,
        "next_page": next_page,
    }


def service(db: DatabaseBackend, seen: list[httpx.Request]) -> OpenAIService:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.params.get("page") is None:
            return httpx.Response(200, json=costs_page("page_2", 1.5), request=request)
        return httpx.Response(200, json=costs_page(None, 2.5), request=request)

    client = OpenAIClient(
        httpx.Client(transport=httpx.MockTransport(handler)), SecretStr("sk-admin")
    )
    return OpenAIService(
        db,
        client,
        stack_id="stack",
        source_id="source",
        lookback_days=9,
        now=lambda: datetime(2026, 9, 10, 12, tzinfo=UTC),
    )


def test_service_follows_pages_and_stores_every_one(db: DatabaseBackend):
    seen: list[httpx.Request] = []

    service(db, seen).fetch_source_data()

    assert len(seen) == 2
    assert seen[0].headers["authorization"] == "Bearer sk-admin"
    assert seen[0].url.params["start_time"] == str(
        int(datetime(2026, 9, 1, tzinfo=UTC).timestamp())
    )
    assert seen[0].url.params["end_time"] == str(
        int(datetime(2026, 9, 11, tzinfo=UTC).timestamp())
    )
    assert seen[0].url.params.get_list("group_by") == ["line_item", "project_id"]
    assert cast(int, db.table(TableName.RAW).count().execute()) == 2
    assert cast(int, db.table(TableName.FACT_BILLING).count().execute()) == 2


def test_sync_marks_the_source_as_connected(db: DatabaseBackend):
    service(db, []).fetch_source_meta()

    assert cast(int, db.table(TableName.DIM_SOURCE_META).count().execute()) == 1
