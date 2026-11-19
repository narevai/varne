from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from typing import Literal, override

from loguru import logger

from varne.config import DEFAULT_LOOKBACK_DAYS, SourceId, SourceType, StackId
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService, utc_now
from varne.providers.types import RowDimSourceMeta
from varne.providers.umami.client import UmamiClient
from varne.providers.umami.transform import transform_pageviews


class UmamiService(ProviderService):
    client: UmamiClient
    website_ids: list[str]

    def __init__(
        self,
        db: DatabaseBackend,
        client: UmamiClient,
        stack_id: StackId,
        source_id: SourceId,
        website_ids: Sequence[str],
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        super().__init__(db, stack_id, source_id, lookback_days, now)
        self.client = client
        self.website_ids = list(website_ids)

    @property
    @override
    def provider(self) -> Literal[SourceType.UMAMI]:
        return SourceType.UMAMI

    @override
    def fetch_source_meta(self) -> None:
        with self.pull():
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
        with self.pull():
            date_from, date_to = self.period()

            for website_id in self.website_ids:
                response = self.client.fetch_pageviews(website_id, date_from, date_to)

                raw = self._raw(response)
                self.store_raw([raw])
                self.store_fact_usage(transform_pageviews(raw))

        logger.info(f"completed fetch source data {self.provider}")
