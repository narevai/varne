from datetime import UTC, datetime
from functools import partial

import httpx2 as httpx
import pytest
from tests.sanitize import sanitize_response
from tests.unit.providers.vercel.policy import policy_vercel_billing

from varne.config import VercelToken
from varne.providers.vercel.client import VercelClient


@pytest.fixture
def vcr_config():
    return {
        "decode_compressed_response": True,
        "filter_headers": ["authorization"],
        "before_record_response": partial(
            sanitize_response, policy=policy_vercel_billing
        ),
    }


@pytest.mark.vcr
def test_fetch_billing(
    http_client: httpx.Client, vercel_token: VercelToken, vercel_team_id: str
):
    client = VercelClient(http_client, api_token=vercel_token)

    billing = client.fetch_billing(
        team_id=vercel_team_id,
        date_from=datetime(2026, 9, 1, tzinfo=UTC),
        date_to=datetime(2026, 9, 10, tzinfo=UTC),
    )

    assert len(billing) > 0
