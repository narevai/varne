import json
from pathlib import Path
from typing import cast

import httpx2 as httpx
import pytest

from varne.settings import Settings
from varne.telemetry import (
    EVENT,
    HOSTNAME,
    INSTANCE_FILE,
    URL,
    instance_id,
    track_server_start,
)


def settings(tmp_path: Path, **changes: object) -> Settings:
    values: dict[str, object] = {
        "database_path": str(tmp_path / "app.duckdb"),
        "enable_telemetry": True,
        "environment": "production",
    }
    return Settings.model_validate(values | changes)


def payload_of(request: httpx.Request) -> dict[str, object]:
    body = cast(dict[str, dict[str, object]], json.loads(request.content))
    return body["payload"]


def recorder() -> tuple[list[httpx.Request], httpx.AsyncClient]:
    sent: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200)

    return sent, httpx.AsyncClient(transport=httpx.MockTransport(handle))


async def test_it_tells_varne_1_apart_from_varne_0(tmp_path: Path):
    sent, client = recorder()

    await track_server_start(settings(tmp_path), client)

    assert len(sent) == 1
    payload = payload_of(sent[0])
    data = cast(dict[str, object], payload["data"])
    assert payload["hostname"] == HOSTNAME == "varne-v1"
    assert payload["url"] == URL == "/v1"
    assert payload["name"] == EVENT == "server_start_v1"
    assert str(data["version"]).startswith("1.")
    assert data["demo"] is False
    assert sent[0].url.path == "/api/send"


async def test_it_sends_nothing_about_what_you_run(tmp_path: Path):
    sent, client = recorder()

    await track_server_start(settings(tmp_path), client)

    data = cast(dict[str, object], payload_of(sent[0])["data"])
    assert set(data) == {"version", "environment", "demo", "instance_id"}


@pytest.mark.parametrize(
    "changes",
    [
        {"enable_telemetry": False},
        {"environment": "development"},
        {"umami_website_id": ""},
    ],
)
async def test_it_can_be_turned_off(tmp_path: Path, changes: dict[str, object]):
    sent, client = recorder()

    await track_server_start(settings(tmp_path, **changes), client)

    assert sent == []


def test_it_is_on_unless_it_is_turned_off():
    assert cast(bool, Settings.model_fields["enable_telemetry"].default) is True


async def test_a_failing_umami_does_not_break_the_start(tmp_path: Path):
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no network", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(refuse))

    await track_server_start(settings(tmp_path), client)


def test_the_instance_id_stays_and_is_not_the_one_of_varne_0(tmp_path: Path):
    first = instance_id(tmp_path)

    assert first
    assert instance_id(tmp_path) == first
    assert (tmp_path / INSTANCE_FILE).read_text() == first
    assert INSTANCE_FILE != ".instance_id"
