from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Literal, override

import httpx2 as httpx
from loguru import logger

from varne.config import SourceId, SourceType, StackId
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService
from varne.providers.openai.client import OpenAIClient
from varne.providers.openai.transform import transform_costs
from varne.providers.openai.types import OpenAICostsPage
from varne.providers.types import RowDimSourceMeta, RowRaw


def _utc_now() -> datetime:
    return datetime.now(UTC)


class OpenAIService(ProviderService):
    client: OpenAIClient
    lookback_days: int
    _now: Callable[[], datetime]

    def __init__(
        self,
        db: DatabaseBackend,
        client: OpenAIClient,
        stack_id: StackId,
        source_id: SourceId,
        lookback_days: int = 30,
        now: Callable[[], datetime] = _utc_now,
    ) -> None:
        super().__init__(db, stack_id, source_id)
        self.client = client
        self.lookback_days = lookback_days
        self._now = now

    @property
    @override
    def provider(self) -> Literal[SourceType.OPENAI]:
        return SourceType.OPENAI

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
        response = self.client.fetch_costs(date_to - timedelta(days=1), date_to)
        raw = self._raw(response)
        self.store_raw([raw])
        self.store_dim_source_meta(
            [
                RowDimSourceMeta(
                    stack_id=self.stack_id,
                    source_id=self.source_id,
                    source_type=self.provider,
                    extracted_at=raw.extracted_at,
                    value_name="costs",
                    value="available",
                )
            ]
        )

    @override
    def fetch_source_data(self) -> None:
        date_from, date_to = self.period()
        page: str | None = None

        while True:
            response = self.client.fetch_costs(date_from, date_to, page)

            raw = self._raw(response)
            self.store_raw([raw])
            self.store_fact_billing(transform_costs(raw))

            costs = OpenAICostsPage.model_validate_json(raw.payload)
            if not costs.has_more or costs.next_page is None:
                break
            page = costs.next_page

        logger.info(f"completed fetch source data {self.provider}")
