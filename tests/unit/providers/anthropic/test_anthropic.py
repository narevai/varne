import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import httpx2 as httpx
import pytest
from pydantic import SecretStr

from varne.config import SourceType, parse_config
from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.anthropic.client import AnthropicClient
from varne.providers.anthropic.service import AnthropicService
from varne.providers.anthropic.transform import transform_cost_report
from varne.providers.types import RowRaw


def result(amount: str, **fields: str | None) -> dict[str, str | None]:
    return {
        "amount": amount,
        "currency": "USD",
        "description": "Claude Opus 5.5 Usage - Input Tokens",
        "cost_type": "tokens",
        "model": "claude-opus-5-5",
        "token_type": "uncached_input_tokens",
        "service_tier": "standard",
        "context_window": "0-200k",
        "workspace_id": "wrkspc_1",
        **fields,
    }


def page(next_page: str | None, amounts: list[str]) -> dict[str, object]:
    return {
        "data": [
            {
                "starting_at": "2026-09-01T00:00:00Z",
                "ending_at": "2026-09-02T00:00:00Z",
                "results": [result(amount) for amount in amounts],
            },
            {
                "starting_at": "2026-09-02T00:00:00Z",
                "ending_at": "2026-09-03T00:00:00Z",
                "results": [],
            },
        ],
        "has_more": next_page is not None,
        "next_page": next_page,
    }


def raw(payload: dict[str, object]) -> RowRaw:
    return RowRaw(
        stack_id="stack",
        source_id="source",
        source_type=SourceType.ANTHROPIC,
        extracted_at=datetime(2026, 9, 10, tzinfo=UTC),
        method="GET",
        url="https://api.anthropic.com/v1/organizations/cost_report",
        payload=json.dumps(payload),
    )


def test_amount_in_cents_becomes_dollars():
    rows = transform_cost_report(raw(page(None, ["123.78912"])))

    assert len(rows) == 1
    assert rows[0].billed_cost == Decimal("1.2378912")
    assert rows[0].effective_cost == rows[0].billed_cost
    assert rows[0].billing_currency == "USD"
    assert rows[0].service_provider_name == "Anthropic"
    assert rows[0].consumed_quantity is None
    assert json.loads(rows[0].tags)["model"] == "claude-opus-5-5"


def test_empty_buckets_give_no_rows():
    assert transform_cost_report(raw({"data": [], "has_more": False})) == []


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
    assert seen[0].url.params["ending_at"] == "2026-09-10T00:00:00+00:00"
    assert cast(int, db.table(TableName.RAW).count().execute()) == 2
    assert cast(int, db.table(TableName.FACT_BILLING).count().execute()) == 2


def test_error_says_what_the_api_answered():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401, json={"error": {"message": "invalid x-api-key"}}, request=request
        )

    client = AnthropicClient(
        httpx.Client(transport=httpx.MockTransport(handler)), SecretStr("x")
    )

    with pytest.raises(httpx.HTTPStatusError, match="invalid x-api-key"):
        client.fetch_cost_report(
            datetime(2026, 9, 1, tzinfo=UTC), datetime(2026, 9, 2, tzinfo=UTC)
        )


def test_config_reads_anthropic_source():
    from varne.config import ConfigAnthropic

    config = parse_config(
        """
stacks:
  - id: s
    name: S
    sources:
      - id: a
        name: A
        type: anthropic
        api_token: sk-ant-admin-x
"""
    )
    source = config.stacks[0].sources[0]

    assert isinstance(source, ConfigAnthropic)
    assert source.lookback_days == 30
    assert source.get_api_token().get_secret_value() == "sk-ant-admin-x"


def test_config_anthropic_needs_exactly_one_token_source():
    with pytest.raises(ValueError, match="Exactly one of api_token"):
        parse_config(
            """
stacks:
  - id: s
    name: S
    sources:
      - id: a
        name: A
        type: anthropic
"""
        )


def test_sync_marks_the_source_as_connected(db: DatabaseBackend):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=page(None, []), request=request)

    client = AnthropicClient(
        httpx.Client(transport=httpx.MockTransport(handler)), SecretStr("x")
    )
    service = AnthropicService(db, client, stack_id="stack", source_id="source")

    service.fetch_source_meta()

    assert cast(int, db.table(TableName.DIM_SOURCE_META).count().execute()) == 1


def test_array_params_use_bracket_names():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=page(None, []), request=request)

    client = AnthropicClient(
        httpx.Client(transport=httpx.MockTransport(handler)), SecretStr("x")
    )
    _ = client.fetch_cost_report(
        datetime(2026, 9, 1, tzinfo=UTC), datetime(2026, 9, 2, tzinfo=UTC)
    )

    assert seen[0].url.params.get_list("group_by[]") == ["description", "workspace_id"]
    assert "group_by" not in seen[0].url.params
