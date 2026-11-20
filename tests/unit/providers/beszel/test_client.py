from datetime import UTC, datetime

import httpx2 as httpx
import pytest
from tests.policy import FieldPolicy, SanitizePolicy
from tests.sanitize import VcrResponse, sanitize_response
from vcr.request import Request

from varne.config import BeszelPassword
from varne.providers.beszel.client import BeszelClient
from varne.providers.beszel.transform import transform_stats
from varne.providers.beszel.types import (
    BeszelContainerStats,
    BeszelPage,
    BeszelSystems,
    BeszelSystemStats,
)

policy_beszel = SanitizePolicy(
    root=FieldPolicy(keep=("page", "perPage", "totalItems", "totalPages")),
    fields=(
        FieldPolicy(
            field="items",
            keep=("id", "name", "status", "created", "system", "type", "stats"),
        ),
    ),
)


def scrub_request(request: Request) -> Request:
    request.body = b"{}"
    return request


def sanitize_beszel(response: VcrResponse) -> VcrResponse:
    body = response.get("body", {}).get("string")
    text = body.decode() if isinstance(body, bytes) else body

    if text is not None and '"token"' in text:
        redacted = '{"token": "redacted"}'
        response["body"] = {
            "string": redacted.encode() if isinstance(body, bytes) else redacted
        }
    else:
        response = sanitize_response(response, policy=policy_beszel)

    response["headers"] = {
        name: value
        for name, value in response.get("headers", {}).items()
        if name.lower() == "content-type"
    }
    return response


@pytest.fixture
def vcr_config() -> dict[str, object]:
    return {
        "decode_compressed_response": True,
        "filter_headers": ["authorization"],
        "match_on": ("method", "scheme", "host", "port", "path"),
        "before_record_request": scrub_request,
        "before_record_response": sanitize_beszel,
    }


@pytest.mark.default_cassette("container_stats.yaml")
@pytest.mark.vcr
def test_fetch_container_stats(
    http_client: httpx.Client,
    beszel_url: str,
    beszel_email: str,
    beszel_password: BeszelPassword,
):
    client = BeszelClient(http_client, beszel_url, beszel_email, beszel_password)
    date_from = datetime(2026, 11, 1, tzinfo=UTC)

    systems_response = client.fetch_systems()
    stats_response = client.fetch_container_stats("1m", date_from, page=1)
    system_response = client.fetch_system_stats("1m", date_from, page=1)

    assert systems_response.is_success
    assert stats_response.is_success
    assert system_response.is_success

    systems = BeszelSystems.model_validate_json(systems_response.text)
    page = BeszelPage[BeszelContainerStats].model_validate_json(stats_response.text)
    machine = BeszelPage[BeszelSystemStats].model_validate_json(system_response.text)
    rows = transform_stats(
        "stack",
        "source",
        datetime(2026, 11, 20, tzinfo=UTC),
        page.items,
        machine.items,
        {system.id: system.name for system in systems.items},
        date_from,
    )

    assert rows
    assert {row.usage_name.split("/")[-1] for row in rows} == {
        "cpu",
        "memory",
        "disk",
        "load",
    }
