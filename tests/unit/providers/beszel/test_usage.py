import json
from datetime import UTC, datetime

import httpx2 as httpx
from pydantic import SecretStr

from varne.providers.beszel.client import BeszelClient
from varne.providers.beszel.usage import BeszelUsage

DATE_FROM = datetime(2026, 9, 8, tzinfo=UTC)


def stats(interval: str, created: str) -> dict[str, object]:
    return {
        "created": created,
        "system": "sys1",
        "type": interval,
        "stats": [{"n": "web", "c": 10, "m": 100}],
    }


def machine(interval: str, created: str) -> dict[str, object]:
    return {
        "created": created,
        "system": "sys1",
        "type": interval,
        "stats": {"cpu": 20, "m": 16, "mu": 4, "du": 10, "la": [1]},
    }


def usage(seen: list[httpx.Request]) -> BeszelUsage:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        path = request.url.path

        body: dict[str, object]
        if path.endswith("auth-with-password"):
            body = {"token": "tok"}
        elif path.endswith("systems/records"):
            body = {"items": [{"id": "sys1", "name": "lab"}]}
        elif path.endswith("containers/records"):
            page = int(request.url.params["page"])
            items = [
                {"name": "web", "image": "nginx:1", "system": "sys1"},
                {"name": "db", "image": "postgres:17", "system": "sys1"},
            ]
            body = {"totalPages": 2, "items": [items[page - 1]]}
        else:
            interval = request.url.params["filter"].split('"')[1]
            created = "2026-09-10 11:30:00.000Z"
            items = (
                [
                    stats("1m", created)
                    if path.endswith("container_stats/records")
                    else machine("1m", created)
                ]
                if interval == "1m"
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
    return BeszelUsage(client)


def test_fetch_logs_in_once_and_asks_for_every_resolution():
    seen: list[httpx.Request] = []

    usage(seen).fetch(DATE_FROM, lambda _: None)

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


def test_login_sends_the_credentials():
    seen: list[httpx.Request] = []

    usage(seen).fetch(DATE_FROM, lambda _: None)

    assert json.loads(seen[0].content) == {
        "identity": "me@example.com",
        "password": "secret",
    }


def test_usage_is_per_system_container_and_metric_with_machine_capacity():
    result = usage([]).fetch(DATE_FROM, lambda _: None)

    names = {(h.system, h.entity, h.metric) for h in result.hours}
    assert names == {
        ("lab", "web", "cpu"),
        ("lab", "web", "memory"),
        ("lab", "system", "cpu"),
        ("lab", "system", "memory"),
        ("lab", "system", "memory_total"),
        ("lab", "system", "disk"),
        ("lab", "system", "load"),
    }


def test_images_of_all_pages_are_keyed_by_system_and_container():
    result = usage([]).fetch(DATE_FROM, lambda _: None)

    assert result.images == {("lab", "web"): "nginx:1", ("lab", "db"): "postgres:17"}


def test_every_response_is_handed_over_to_be_kept():
    responses: list[httpx.Response] = []

    usage([]).fetch(DATE_FROM, responses.append)

    # systems + 2 container pages + 5 container + 5 system stat pages
    assert len(responses) == 13


def test_systems_are_listed_by_name():
    assert usage([]).systems(lambda _: None) == ["lab"]


def test_creating_it_does_not_call_the_hub():
    seen: list[httpx.Request] = []

    usage(seen)

    assert seen == []
