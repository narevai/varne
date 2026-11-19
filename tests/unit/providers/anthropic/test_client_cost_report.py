from datetime import UTC, datetime

import httpx2 as httpx
import pytest
from pydantic import SecretStr
from tests.policy import FieldPolicy, SanitizePolicy
from tests.sanitize import VcrResponse, sanitize_response
from tests.unit.providers.anthropic.test_transform import page

from varne.config import AnthropicToken, SourceType
from varne.providers.anthropic.client import AnthropicClient
from varne.providers.anthropic.transform import transform_cost_report
from varne.providers.types import RowRaw

policy_anthropic_cost_report = SanitizePolicy(
    fields=(
        FieldPolicy(
            field="data",
            keep=("starting_at", "ending_at"),
        ),
        FieldPolicy(
            field="results",
            keep=(
                "amount",
                "currency",
                "description",
                "cost_type",
                "model",
                "token_type",
                "service_tier",
                "context_window",
            ),
        ),
    ),
)


def sanitize_cost_report(response: VcrResponse) -> VcrResponse:
    response = sanitize_response(response, policy=policy_anthropic_cost_report)
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
        "filter_headers": ["x-api-key", "authorization"],
        "match_on": ("method", "scheme", "host", "port", "path"),
        "before_record_response": sanitize_cost_report,
    }


@pytest.mark.default_cassette("cost_report.yaml")
@pytest.mark.vcr
def test_fetch_cost_report(http_client: httpx.Client, anthropic_token: AnthropicToken):
    client = AnthropicClient(http_client, api_token=anthropic_token)

    response = client.fetch_cost_report(
        date_from=datetime(2026, 10, 18, tzinfo=UTC),
        date_to=datetime(2026, 11, 17, tzinfo=UTC),
    )

    assert response.is_success

    rows = transform_cost_report(
        RowRaw(
            stack_id="stack",
            source_id="source",
            source_type=SourceType.ANTHROPIC,
            extracted_at=datetime(2026, 11, 18, tzinfo=UTC),
            method="GET",
            url=str(response.request.url),
            payload=response.text,
        )
    )
    assert all(row.billing_currency == "USD" for row in rows)


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
