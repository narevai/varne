import httpx2 as httpx
import pytest
from pydantic import SecretStr

from varne.providers.vercel.client import VercelClient


def failing_http() -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"code": "web_analytics_not_enabled"}},
            request=request,
        )

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_vercel_error_says_what_the_api_answered():
    client = VercelClient(failing_http(), api_token=SecretStr("x"))

    with pytest.raises(httpx.HTTPStatusError, match="web_analytics_not_enabled"):
        client.fetch_projects()
