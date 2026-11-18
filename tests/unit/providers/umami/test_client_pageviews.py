from datetime import UTC, datetime

import httpx2 as httpx
import pytest
from tests.policy import FieldPolicy, SanitizePolicy
from tests.sanitize import VcrResponse, sanitize_response

from varne.config import SourceType, UmamiToken
from varne.providers.types import RowRaw
from varne.providers.umami.client import UmamiClient
from varne.providers.umami.transform import transform_pageviews

policy_umami_pageviews = SanitizePolicy(
    fields=(
        FieldPolicy(field="pageviews", keep=("x", "y")),
        FieldPolicy(field="sessions", keep=("x", "y")),
    ),
)


def sanitize_pageviews(response: VcrResponse) -> VcrResponse:
    response = sanitize_response(response, policy=policy_umami_pageviews)
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
        "filter_headers": ["authorization", "x-umami-api-key"],
        "match_on": ("method", "scheme", "host", "port", "path"),
        "before_record_response": sanitize_pageviews,
    }


@pytest.mark.default_cassette("pageviews.yaml")
@pytest.mark.vcr
def test_fetch_pageviews(
    http_client: httpx.Client, umami_token: UmamiToken, umami_website_id: str
):
    client = UmamiClient(http_client, api_token=umami_token)

    response = client.fetch_pageviews(
        website_id=umami_website_id,
        date_from=datetime(2026, 10, 18, tzinfo=UTC),
        date_to=datetime(2026, 11, 17, tzinfo=UTC),
    )

    assert response.is_success

    rows = transform_pageviews(
        RowRaw(
            stack_id="stack",
            source_id="source",
            source_type=SourceType.UMAMI,
            extracted_at=datetime(2026, 11, 18, tzinfo=UTC),
            method="GET",
            url=str(response.request.url),
            payload=response.text,
        )
    )
    assert {row.usage_name for row in rows} <= {"pageviews", "sessions"}
