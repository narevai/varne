import json
from datetime import UTC, datetime
from typing import cast

import httpx2 as httpx
from pydantic import SecretStr

from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.beszel.client import BeszelClient
from varne.providers.beszel.service import BeszelService


def stats(interval: str, created: str) -> dict[str, object]:
    return {
        "created": created,
        "system": "sys1",
        "type": interval,
        "stats": [{"n": "web", "c": 10, "m": 100}],
    }


def service(db: DatabaseBackend, seen: list[httpx.Request]) -> BeszelService:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        path = request.url.path

        body: dict[str, object]
        if path.endswith("auth-with-password"):
            body = {"token": "tok"}
        elif path.endswith("systems/records"):
            body = {"items": [{"id": "sys1", "name": "lab"}]}
        else:
            interval = request.url.params["filter"].split('"')[1]
            items = (
                [stats("1m", "2026-09-10 11:30:00.000Z")]
                if interval == "1m" and path.endswith("container_stats/records")
                else []
            )
            body = {"totalPages": 1 if items else 0, "items": items}

        return httpx.Response(200, content=json.dumps(body), request=request)

    client = BeszelClient(
        httpx.Client(transport=httpx.MockTransport(handler)),
        "http://hub:8090/",
        "me@example.com",
        SecretStr("secret"),
    )
    return BeszelService(
        db,
        client,
        stack_id="stack",
        source_id="source",
        lookback_days=2,
        now=lambda: datetime(2026, 9, 10, 12, tzinfo=UTC),
    )


def test_pull_logs_in_once_and_asks_for_every_resolution(db: DatabaseBackend):
    seen: list[httpx.Request] = []

    service(db, seen).fetch_source_data()

    assert [r.url.path for r in seen].count(
        "/api/collections/users/auth-with-password"
    ) == 1
    filters = [
        r.url.params["filter"]
        for r in seen
        if r.url.path.endswith("container_stats/records")
    ]
    assert [f.split('"')[1] for f in filters] == ["1m", "10m", "20m", "120m", "480m"]
    assert sum(r.url.path.endswith("system_stats/records") for r in seen) == 5
    assert all('created>="2026-09-08 00:00:00.000Z"' in f for f in filters)
    assert seen[-1].headers["authorization"] == "tok"


def test_login_sends_the_credentials(db: DatabaseBackend):
    seen: list[httpx.Request] = []

    service(db, seen).fetch_source_data()

    assert json.loads(seen[0].content) == {
        "identity": "me@example.com",
        "password": "secret",
    }


def test_usage_is_stored_per_container_and_metric(db: DatabaseBackend):
    service(db, []).fetch_source_data()

    names = db.table(TableName.FACT_USAGE).usage_name.execute().tolist()  # pyright: ignore[reportUnknownVariableType]
    assert sorted(cast(list[str], names)) == ["lab/web/cpu", "lab/web/memory"]
    # systems + five container pages + five system pages
    assert cast(int, db.table(TableName.RAW).count().execute()) == 11


def test_sync_stores_system_names(db: DatabaseBackend):
    service(db, []).fetch_source_meta()

    values = db.table(TableName.DIM_SOURCE_META).value.execute().tolist()  # pyright: ignore[reportUnknownVariableType]
    assert cast(list[str], values) == ["lab"]


def test_creating_the_service_does_not_call_the_hub(db: DatabaseBackend):
    seen: list[httpx.Request] = []

    service(db, seen)

    assert seen == []
