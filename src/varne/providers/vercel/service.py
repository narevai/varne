from datetime import UTC, datetime
from typing import Literal, override

import httpx2 as httpx
from loguru import logger

from varne.config import SourceId, SourceType, StackId
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService
from varne.providers.types import RowRaw
from varne.providers.vercel.client import VercelClient
from varne.providers.vercel.transform import transform_meta


class VercelService(ProviderService):
    client: VercelClient

    def __init__(
        self,
        db: DatabaseBackend,
        client: VercelClient,
        stack_id: StackId,
        source_id: SourceId,
    ) -> None:
        super().__init__(db, stack_id, source_id)
        self.client = client

    @property
    @override
    def provider(self) -> Literal[SourceType.VERCEL]:
        return SourceType.VERCEL

    @override
    def fetch_and_store(self) -> None:
        response: httpx.Response = self.client.fetch_projects()

        raw = RowRaw(
            stack_id=self.stack_id,
            source_id=self.source_id,
            source_type=self.provider,
            extracted_at=datetime.now(UTC),
            method=response.request.method,
            url=str(response.request.url),
            payload=response.text,
        )
        self.store_raw([raw])

        meta = transform_meta(raw)
        self.store_staging(meta)
        logger.info(f"completed fetch and store for {self.provider}")
