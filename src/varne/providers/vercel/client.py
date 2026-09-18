from datetime import datetime
from typing import override

import httpx2 as httpx

from varne.config import VercelToken
from varne.providers.base import ProviderClient


class VercelClient(ProviderClient):
    api_token: VercelToken

    def __init__(self, http: httpx.Client, api_token: VercelToken):
        super().__init__(http)
        self.api_token = api_token

    @property
    @override
    def base_url(self) -> httpx.URL:
        return httpx.URL("https://api.vercel.com")

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token.get_secret_value()}",
        }

    def fetch_projects(self) -> httpx.Response:
        response = self.http.get(
            url=self.base_url.join("/v10/projects"), headers=self.headers
        )
        response.raise_for_status()

        return response

    def fetch_billing(
        self,
        team_id: str,
        date_from: datetime,
        date_to: datetime,
    ) -> httpx.Response:
        response = self.http.get(
            url=self.base_url.join("/v1/billing/charges"),
            headers=self.headers,
            params={
                "teamId": team_id,
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
        )

        response.raise_for_status()

        return response

    def fetch_web_analytics_visits_count(
        self,
        team_id: str,
        project_id: str,
        date_from: datetime,
        date_to: datetime,
    ) -> httpx.Response:
        response = self.http.get(
            url=self.base_url.join("/v1/query/web-analytics/visits/count"),
            headers=self.headers,
            params={
                "teamId": team_id,
                "projectId": project_id,
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
        )

        response.raise_for_status()

        return response

    def fetch_web_analytics_visits_aggregate(
        self,
        team_id: str,
        project_id: str,
        date_from: datetime,
        date_to: datetime,
    ) -> httpx.Response:
        response = self.http.get(
            url=self.base_url.join("/v1/query/web-analytics/visits/aggregate"),
            headers=self.headers,
            params={
                "teamId": team_id,
                "projectId": project_id,
                "since": date_from.isoformat(),
                "until": date_to.isoformat(),
                "by": ["day"],
            },
        )

        response.raise_for_status()

        return response
