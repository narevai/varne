from datetime import UTC, datetime

import httpx2 as httpx
import pytest
from pydantic import SecretStr

from varne.providers.anthropic.client import AnthropicClient
from varne.providers.openai.client import OpenAIClient
from varne.providers.umami.client import UmamiClient
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


def test_anthropic_error_says_what_the_api_answered():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401, json={"error": {"message": "invalid x-api-key"}}, request=request
        )

    client = AnthropicClient(
        httpx.Client(transport=httpx.MockTransport(handler)), SecretStr("x")
    )

    with pytest.raises(httpx.HTTPStatusError, match="invalid x-api-key"):
        client.fetch_cost_report(
            datetime(2026, 9, 1, tzinfo=UTC), datetime(2026, 9, 2, tzinfo=UTC)
        )


def test_openai_error_says_what_the_api_answered():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401, json={"error": {"message": "Incorrect API key"}}, request=request
        )

    client = OpenAIClient(
        httpx.Client(transport=httpx.MockTransport(handler)), SecretStr("x")
    )

    with pytest.raises(httpx.HTTPStatusError, match="Incorrect API key"):
        client.fetch_costs(
            datetime(2026, 9, 1, tzinfo=UTC), datetime(2026, 9, 2, tzinfo=UTC)
        )


def test_umami_error_says_what_the_api_answered():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "Unauthorized"}, request=request)

    client = UmamiClient(
        httpx.Client(transport=httpx.MockTransport(handler)), SecretStr("x")
    )

    with pytest.raises(httpx.HTTPStatusError, match="Unauthorized"):
        client.fetch_pageviews(
            "w1", datetime(2026, 9, 1, tzinfo=UTC), datetime(2026, 9, 2, tzinfo=UTC)
        )
