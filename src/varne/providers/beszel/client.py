from datetime import UTC, datetime
from typing import override

import httpx2 as httpx

from varne.config import BeszelPassword
from varne.providers.base import ProviderClient
from varne.providers.beszel.types import BeszelAuth

PER_PAGE = 100


class BeszelClient(ProviderClient):
    url: str
    email: str
    password: BeszelPassword
    _token: str | None

    def __init__(
        self, http: httpx.Client, url: str, email: str, password: BeszelPassword
    ):
        super().__init__(http)
        self.url = url
        self.email = email
        self.password = password
        self._token = None

    @property
    @override
    def base_url(self) -> httpx.URL:
        return httpx.URL(self.url.rstrip("/") + "/")

    def authenticate(self) -> str:
        if self._token is None:
            response = self.http.post(
                url=self.base_url.join("api/collections/users/auth-with-password"),
                json={
                    "identity": self.email,
                    "password": self.password.get_secret_value(),
                },
            )
            self.raise_for_status(response)
            self._token = BeszelAuth.model_validate_json(response.text).token

        return self._token

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": self.authenticate()}

    def fetch_systems(self) -> httpx.Response:
        response = self.http.get(
            url=self.base_url.join("api/collections/systems/records"),
            headers=self.headers,
            params={"perPage": 500},
        )
        self.raise_for_status(response)

        return response

    def fetch_containers(self, page: int) -> httpx.Response:
        response = self.http.get(
            url=self.base_url.join("api/collections/containers/records"),
            headers=self.headers,
            params={"perPage": PER_PAGE, "page": page},
        )
        self.raise_for_status(response)

        return response

    def fetch_stats(
        self, collection: str, interval: str, date_from: datetime, page: int
    ) -> httpx.Response:
        created = date_from.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S.000Z")
        response = self.http.get(
            url=self.base_url.join(f"api/collections/{collection}/records"),
            headers=self.headers,
            params={
                "filter": f'type="{interval}" && created>="{created}"',
                "sort": "created",
                "perPage": PER_PAGE,
                "page": page,
            },
        )
        self.raise_for_status(response)

        return response

    def fetch_container_stats(
        self, interval: str, date_from: datetime, page: int
    ) -> httpx.Response:
        return self.fetch_stats("container_stats", interval, date_from, page)

    def fetch_system_stats(
        self, interval: str, date_from: datetime, page: int
    ) -> httpx.Response:
        return self.fetch_stats("system_stats", interval, date_from, page)
