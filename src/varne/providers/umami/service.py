from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from typing import Literal, override

import httpx2 as httpx
from loguru import logger

from varne.config import SourceId, SourceType, StackId
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService
from varne.providers.types import RowDimSourceMeta, RowRaw
from varne.providers.umami.client import UmamiClient
from varne.providers.umami.transform import transform_pageviews


def _utc_now() -> datetime:
    return datetime.now(UTC)


class UmamiService(ProviderService):
    client: UmamiClient
    website_ids: list[str]
    lookback_days: int
    _now: Callable[[], datetime]

    def __init__(
        self,
        db: DatabaseBackend,
        client: UmamiClient,
        stack_id: StackId,
        source_id: SourceId,
        website_ids: Sequence[str],
        lookback_days: int = 30,
        now: Callable[[], datetime] = _utc_now,
    ) -> None:
        super().__init__(db, stack_id, source_id)
        self.client = client
        self.website_ids = list(website_ids)
        self.lookback_days = lookback_days
        self._now = now

    @property
    @override
    def provider(self) -> Literal[SourceType.UMAMI]:
        return SourceType.UMAMI

    def period(self) -> tuple[datetime, datetime]:
        date_to = (
            self._now()
            .astimezone(UTC)
            .replace(hour=0, minute=0, second=0, microsecond=0)
        )
        return date_to - timedelta(days=self.lookback_days), date_to

    def _raw(self, response: httpx.Response) -> RowRaw:
        return RowRaw(
            stack_id=self.stack_id,
            source_id=self.source_id,
            source_type=self.provider,
            extracted_at=self._now(),
            method=response.request.method,
            url=str(response.request.url),
            payload=response.text,
        )

    @override
    def fetch_source_meta(self) -> None:
        _, date_to = self.period()

        for website_id in self.website_ids:
            response = self.client.fetch_pageviews(
                website_id, date_to - timedelta(days=1), date_to
            )

            raw = self._raw(response)
            self.store_raw([raw])
            self.store_dim_source_meta(
                [
                    RowDimSourceMeta(
                        stack_id=self.stack_id,
                        source_id=self.source_id,
                        source_type=self.provider,
                        extracted_at=raw.extracted_at,
                        value_name="website_id",
                        value=website_id,
                    )
                ]
            )

        logger.info(f"completed fetch source meta {self.provider}")

    @override
    def fetch_source_data(self) -> None:
        date_from, date_to = self.period()

        for website_id in self.website_ids:
            response = self.client.fetch_pageviews(website_id, date_from, date_to)

            raw = self._raw(response)
            self.store_raw([raw])
            self.store_fact_usage(transform_pageviews(raw))

        logger.info(f"completed fetch source data {self.provider}")
