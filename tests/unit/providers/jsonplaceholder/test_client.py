import httpx2 as httpx
import pytest

from varne.providers.jsonplaceholder.client import JsonPlaceholderClient


@pytest.mark.vcr
def test_fetch(http_client: httpx.Client):
    client = JsonPlaceholderClient(http_client)

    response = client.fetch_posts()

    assert response.is_success
