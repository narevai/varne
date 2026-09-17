from datetime import UTC, datetime
from typing import Literal, override

import httpx2 as httpx
from loguru import logger

from varne.config import SourceId, SourceType, StackId
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService
from varne.providers.jsonplaceholder.client import JsonPlaceholderClient
from varne.providers.jsonplaceholder.transform import transform_posts
from varne.providers.types import RowDimSourceMeta, RowRaw


class JsonPlaceholderService(ProviderService):
    client: JsonPlaceholderClient

    def __init__(
        self,
        db: DatabaseBackend,
        client: JsonPlaceholderClient,
        stack_id: StackId,
        source_id: SourceId,
    ):
        super().__init__(db, stack_id, source_id)
        self.client = client

    @property
    @override
    def provider(self) -> Literal[SourceType.JSONPLACEHOLDER]:
        return SourceType.JSONPLACEHOLDER

    @override
    def fetch_and_store(self) -> None:
        response: httpx.Response = self.client.fetch_posts()
        posts_row = RowRaw(
            stack_id=self.stack_id,
            source_id=self.source_id,
            source_type=self.provider,
            extracted_at=datetime.now(UTC),
            method=response.request.method,
            url=str(response.request.url),
            payload=response.text,
        )

        self.store_raw([posts_row])
        posts_transformed: list[RowDimSourceMeta] = transform_posts(posts_row)
        self.store_staging(posts_transformed)
        logger.info("completed fetch and store for jsonplaceholder")
