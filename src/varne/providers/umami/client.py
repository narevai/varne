from datetime import datetime
from typing import override

import httpx2 as httpx

from varne.config import UmamiToken
from varne.providers.base import ProviderClient


class UmamiClient(ProviderClient):
    api_token: UmamiToken

    def __init__(self, http: httpx.Client, api_token: UmamiToken):
        super().__init__(http)
        self.api_token = api_token

    @property
    @override
    def base_url(self) -> httpx.URL:
        return httpx.URL("https://api.umami.is/v1/")

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token.get_secret_value()}",
        }

    def fetch_pageviews(
        self,
        website_id: str,
        date_from: datetime,
        date_to: datetime,
    ) -> httpx.Response:
        response = self.http.get(
            url=self.base_url.join(f"websites/{website_id}/pageviews"),
            headers=self.headers,
            params={
                "startAt": int(date_from.timestamp() * 1000),
                "endAt": int(date_to.timestamp() * 1000),
                "unit": "day",
                "timezone": "UTC",
            },
        )
        self.raise_for_status(response)

        return response
