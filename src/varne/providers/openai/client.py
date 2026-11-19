from datetime import datetime
from typing import override

import httpx2 as httpx

from varne.config import OpenAIToken
from varne.providers.base import ProviderClient


class OpenAIClient(ProviderClient):
    api_token: OpenAIToken

    def __init__(self, http: httpx.Client, api_token: OpenAIToken):
        super().__init__(http)
        self.api_token = api_token

    @property
    @override
    def base_url(self) -> httpx.URL:
        return httpx.URL("https://api.openai.com")

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token.get_secret_value()}",
        }

    def fetch_costs(
        self,
        date_from: datetime,
        date_to: datetime,
        page: str | None = None,
    ) -> httpx.Response:
        params: dict[str, str | int | list[str]] = {
            "start_time": int(date_from.timestamp()),
            "end_time": int(date_to.timestamp()),
            "bucket_width": "1d",
            "group_by": ["line_item", "project_id"],
            "limit": 180,
        }
        if page is not None:
            params["page"] = page

        response = self.http.get(
            url=self.base_url.join("/v1/organization/costs"),
            headers=self.headers,
            params=params,
        )

        self.raise_for_status(response)

        return response
