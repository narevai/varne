from datetime import UTC, datetime
from typing import Literal, override

import httpx2 as httpx
from loguru import logger

from varne.config import SourceId, SourceType, StackId
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService
from varne.providers.types import RowRaw
from varne.providers.vercel.client import VercelClient
from varne.providers.vercel.transform import (
    transform_analytics_aggregate,
    transform_billing,
    transform_meta,
)


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
    def fetch_source_meta(self) -> None:
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
        self.store_dim_source_meta(meta)
        logger.info(f"completed fetch source meta {self.provider}")

    @override
    def fetch_source_data(self) -> None:
        self._fetch_source_billing()
        self._fetch_source_usage()

        logger.info(f"completed fetch source data {self.provider}")

    def _fetch_source_billing(self) -> None:
        team_id = "team_4lN90TlRlQzpFGhMLIoTTS9D"
        date_from = datetime(2026, 9, 1, tzinfo=UTC)
        date_to = datetime(2026, 9, 10, tzinfo=UTC)

        response: httpx.Response = self.client.fetch_billing(
            team_id=team_id, date_from=date_from, date_to=date_to
        )

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

        billing = transform_billing(raw)
        self.store_fact_billing(billing)

    def _fetch_source_usage(self) -> None:
        project_id = "prj_5LAip7eW0S0iDBoLNDwa9gMTye78"
        team_id = "team_4lN90TlRlQzpFGhMLIoTTS9D"
        date_from = datetime(2026, 9, 1, tzinfo=UTC)
        date_to = datetime(2026, 9, 10, tzinfo=UTC)

        response: httpx.Response = self.client.fetch_web_analytics_visits_aggregate(
            team_id=team_id, project_id=project_id, date_from=date_from, date_to=date_to
        )

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

        usage = transform_analytics_aggregate(raw)
        self.store_fact_usage(usage)
