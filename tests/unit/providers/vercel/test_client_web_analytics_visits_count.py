from datetime import UTC, datetime
from functools import partial

import httpx2 as httpx
import pytest
from tests.policy import FieldPolicy, SanitizePolicy
from tests.sanitize import sanitize_response

from varne.config import VercelToken
from varne.providers.vercel.client import VercelClient

policy_vercel_analytics = SanitizePolicy(
    root=FieldPolicy(
        keep=(
            "version",
            "query",
            "data",
        ),
    ),
)


@pytest.fixture
def vcr_config():
    return {
        "decode_compressed_response": True,
        "filter_headers": ["authorization"],
        "before_record_response": partial(
            sanitize_response, policy=policy_vercel_analytics
        ),
    }


@pytest.mark.vcr
def test_fetch_web_analytics_visits_count(
    http_client: httpx.Client,
    vercel_token: VercelToken,
    vercel_team_id: str,
    vercel_project_id: str,
):
    client = VercelClient(http_client, api_token=vercel_token)

    web_analytics = client.fetch_web_analytics_visits_count(
        team_id=vercel_team_id,
        project_id=vercel_project_id,
        date_from=datetime(2026, 9, 1, tzinfo=UTC),
        date_to=datetime(2026, 9, 10, tzinfo=UTC),
    )

    assert len(web_analytics) > 0
