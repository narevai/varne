from datetime import datetime
from typing import override

import httpx2 as httpx

from varne.config import AnthropicToken
from varne.providers.base import ProviderClient


class AnthropicClient(ProviderClient):
    api_token: AnthropicToken

    def __init__(self, http: httpx.Client, api_token: AnthropicToken):
        super().__init__(http)
        self.api_token = api_token

    @property
    @override
    def base_url(self) -> httpx.URL:
        return httpx.URL("https://api.anthropic.com")

    @property
    def headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_token.get_secret_value(),
            "anthropic-version": "2023-06-01",
        }

    def fetch_cost_report(
        self,
        date_from: datetime,
        date_to: datetime,
        page: str | None = None,
    ) -> httpx.Response:
        params: dict[str, str | int | list[str]] = {
            "starting_at": date_from.isoformat(),
            "ending_at": date_to.isoformat(),
            "bucket_width": "1d",
            "group_by[]": ["description", "workspace_id"],
            "limit": 31,
        }
        if page is not None:
            params["page"] = page

        response = self.http.get(
            url=self.base_url.join("/v1/organizations/cost_report"),
            headers=self.headers,
            params=params,
        )

        self.raise_for_status(response)

        return response
