from datetime import UTC, datetime
from typing import Literal, override

from loguru import logger

from varne.config import SourceId, StackId
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService
from varne.providers.jsonplaceholder.client import JsonPlaceholderClient
from varne.providers.jsonplaceholder.transform import transform_posts
from varne.providers.types import RowRaw, RowStaging


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
    def provider(self) -> Literal["jsonplaceholder"]:
        return "jsonplaceholder"

    @override
    def fetch_and_store(self) -> None:
        posts_payload: str = self.client.fetch_posts()
        posts_row = RowRaw(
            stack_id=self.stack_id,
            source_id=self.source_id,
            provider=self.provider,
            event_time=datetime.now(UTC),
            payload=posts_payload,
        )

        self.store_raw([posts_row])
        posts_transformed: list[RowStaging] = transform_posts(posts_row)
        self.store_staging(posts_transformed)
        logger.info("completed fetch and store for jsonplaceholder")
