from typing import override

import httpx2 as httpx

from varne.providers.base import ProviderClient


class JsonPlaceholderClient(ProviderClient):
    @property
    @override
    def base_url(self) -> httpx.URL:
        return httpx.URL("https://jsonplaceholder.typicode.com")

    def fetch_posts(self) -> str:
        response = self.http.get(self.base_url.join("/posts"))

        response.raise_for_status()

        return response.text
