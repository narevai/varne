from datetime import datetime
from typing import override

import httpx2 as httpx

from varne.config import VercelToken
from varne.providers.base import ProviderClient


class VercelClient(ProviderClient):
    api_token: VercelToken

    def __init__(self, client: httpx.Client, api_token: VercelToken):
        super().__init__(client)
        self.api_token = api_token

    @property
    @override
    def base_url(self) -> str:
        return "https://api.vercel.com"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
        }

    def fetch_projects(self) -> str:
        response = self.http.get(
            url=f"{self.base_url}/v10/projects", headers=self.headers
        )
        response.raise_for_status()

        return response.text

    def fetch_billing(
        self,
        team_id: str,
        date_from: datetime,
        date_to: datetime,
    ) -> str:
        response = self.http.get(
            url=f"{self.base_url}/v1/billing/charges",
            headers=self.headers,
            params={
                "teamId": team_id,
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
        )

        return response.text
