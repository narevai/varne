from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Literal, override

from loguru import logger

from varne.config import DEFAULT_LOOKBACK_DAYS, SourceId, SourceType, StackId
from varne.db.types import DatabaseBackend
from varne.providers.anthropic.client import AnthropicClient
from varne.providers.anthropic.transform import transform_cost_report
from varne.providers.anthropic.types import AnthropicCostReport
from varne.providers.base import ProviderService, utc_now
from varne.providers.types import RowDimSourceMeta


class AnthropicService(ProviderService):
    client: AnthropicClient

    def __init__(
        self,
        db: DatabaseBackend,
        client: AnthropicClient,
        stack_id: StackId,
        source_id: SourceId,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        super().__init__(db, stack_id, source_id, lookback_days, now)
        self.client = client

    @property
    @override
    def provider(self) -> Literal[SourceType.ANTHROPIC]:
        return SourceType.ANTHROPIC

    @override
    def fetch_source_meta(self) -> None:
        with self.pull():
            _, date_to = self.period()
            response = self.client.fetch_cost_report(
                date_to - timedelta(days=1), date_to
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
                        value_name="cost_report",
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
                response = self.client.fetch_cost_report(date_from, date_to, page)

                raw = self._raw(response)
                self.store_raw([raw])
                self.store_fact_billing(transform_cost_report(raw))

                report = AnthropicCostReport.model_validate_json(raw.payload)
                if not report.has_more or report.next_page is None:
                    break
                page = report.next_page

        logger.info(f"completed fetch source data {self.provider}")
