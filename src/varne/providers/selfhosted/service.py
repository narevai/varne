from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Literal, override

from loguru import logger

from varne.config import DEFAULT_LOOKBACK_DAYS, SourceId, SourceType, StackId
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService, utc_now
from varne.providers.selfhosted.rates import CostLine
from varne.providers.selfhosted.transform import CURRENCY, transform_costs
from varne.providers.types import RowDimSourceMeta

DISPLAY_PRECISION = Decimal("0.000001")


class SelfHostedService(ProviderService):
    lines: list[CostLine]

    def __init__(
        self,
        db: DatabaseBackend,
        stack_id: StackId,
        source_id: SourceId,
        lines: list[CostLine],
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        super().__init__(db, stack_id, source_id, lookback_days, now)
        self.lines = lines

    @property
    @override
    def provider(self) -> Literal[SourceType.SELFHOSTED]:
        return SourceType.SELFHOSTED

    def _meta(self, extracted_at: datetime, name: str, value: str) -> RowDimSourceMeta:
        return RowDimSourceMeta(
            stack_id=self.stack_id,
            source_id=self.source_id,
            source_type=self.provider,
            extracted_at=extracted_at,
            value_name=name,
            value=value,
        )

    @override
    def fetch_source_meta(self) -> None:
        with self.pull():
            extracted_at = self._extracted_at()

            meta: list[RowDimSourceMeta] = []
            for line in self.lines:
                per_hour = line.cost_per_hour.quantize(DISPLAY_PRECISION)
                meta.append(
                    self._meta(
                        extracted_at,
                        f"{line.service_name} per hour",
                        f"{per_hour} {CURRENCY}",
                    )
                )

            self.store_dim_source_meta(meta)

        logger.info(f"completed fetch source meta {self.provider}")

    @override
    def fetch_source_data(self) -> None:
        with self.pull():
            date_from, date_to = self.period()

            self.store_fact_billing(
                transform_costs(
                    self.stack_id,
                    self.source_id,
                    self._extracted_at(),
                    self.lines,
                    date_from,
                    date_to,
                )
            )

        logger.info(f"completed fetch source data {self.provider}")
