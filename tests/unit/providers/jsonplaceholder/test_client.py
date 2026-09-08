import httpx2 as httpx
import pytest

from varne.providers.jsonplaceholder.client import JsonPlaceholderClient


@pytest.mark.vcr
def test_fetch(http_client: httpx.Client):
    client = JsonPlaceholderClient(http_client)

    posts = client.fetch_posts()

    assert len(posts) > 0
