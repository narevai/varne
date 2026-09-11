from functools import partial

import httpx2 as httpx
import pytest
from tests.sanitize import sanitize_response
from tests.unit.providers.vercel.policy import policy_vercel_projects

from varne.config import VercelToken
from varne.providers.vercel.client import VercelClient


@pytest.fixture
def vcr_config():
    return {
        "decode_compressed_response": True,
        "filter_headers": ["authorization"],
        "before_record_response": partial(
            sanitize_response, policy=policy_vercel_projects
        ),
    }


@pytest.mark.vcr
def test_fetch_projects(http_client: httpx.Client, vercel_token: VercelToken):
    client = VercelClient(http_client, api_token=vercel_token)

    projects = client.fetch_projects()

    assert len(projects) > 0
