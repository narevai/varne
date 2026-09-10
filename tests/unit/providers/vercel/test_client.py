import httpx2 as httpx
import pytest

from varne.config import VercelToken
from varne.providers.vercel.client import VercelClient


@pytest.mark.vcr
def test_fetch_projects(http_client: httpx.Client, vercel_token: VercelToken):
    client = VercelClient(http_client, api_token=vercel_token)

    projects = client.fetch_projects()

    assert len(projects) > 0
