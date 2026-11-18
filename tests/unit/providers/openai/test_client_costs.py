from datetime import UTC, datetime

import httpx2 as httpx
import pytest
from tests.policy import FieldPolicy, SanitizePolicy
from tests.sanitize import VcrResponse, sanitize_response

from varne.config import OpenAIToken, SourceType
from varne.providers.openai.client import OpenAIClient
from varne.providers.openai.transform import transform_costs
from varne.providers.types import RowRaw

policy_openai_costs = SanitizePolicy(
    fields=(
        FieldPolicy(field="data", keep=("start_time", "end_time")),
        FieldPolicy(
            field="results",
            keep=("amount", "line_item", "quantity", "quantity_unit"),
        ),
    ),
)


def sanitize_costs(response: VcrResponse) -> VcrResponse:
    response = sanitize_response(response, policy=policy_openai_costs)
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
        "before_record_response": sanitize_costs,
    }


@pytest.mark.default_cassette("costs.yaml")
@pytest.mark.vcr
def test_fetch_costs(http_client: httpx.Client, openai_token: OpenAIToken):
    client = OpenAIClient(http_client, api_token=openai_token)

    response = client.fetch_costs(
        date_from=datetime(2026, 10, 18, tzinfo=UTC),
        date_to=datetime(2026, 11, 17, tzinfo=UTC),
    )

    assert response.is_success

    rows = transform_costs(
        RowRaw(
            stack_id="stack",
            source_id="source",
            source_type=SourceType.OPENAI,
            extracted_at=datetime(2026, 11, 18, tzinfo=UTC),
            method="GET",
            url=str(response.request.url),
            payload=response.text,
        )
    )
    assert all(row.billing_currency == "USD" for row in rows)
