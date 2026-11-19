from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Literal, override

from loguru import logger

from varne.config import DEFAULT_LOOKBACK_DAYS, SourceId, SourceType, StackId
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService, utc_now
from varne.providers.openai.client import OpenAIClient
from varne.providers.openai.transform import transform_costs
from varne.providers.openai.types import OpenAICostsPage
from varne.providers.types import RowDimSourceMeta


class OpenAIService(ProviderService):
    client: OpenAIClient

    def __init__(
        self,
        db: DatabaseBackend,
        client: OpenAIClient,
        stack_id: StackId,
        source_id: SourceId,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        super().__init__(db, stack_id, source_id, lookback_days, now)
        self.client = client

    @property
    @override
    def provider(self) -> Literal[SourceType.OPENAI]:
        return SourceType.OPENAI

    @override
    def fetch_source_meta(self) -> None:
        with self.pull():
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
        with self.pull():
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
