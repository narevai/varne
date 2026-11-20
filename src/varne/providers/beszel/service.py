from collections.abc import Callable
from datetime import datetime
from typing import Literal, override

from loguru import logger

from varne.config import DEFAULT_LOOKBACK_DAYS, SourceId, SourceType, StackId
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService, utc_now
from varne.providers.beszel.client import BeszelClient
from varne.providers.beszel.transform import transform_stats
from varne.providers.beszel.types import (
    INTERVALS,
    BeszelContainerStats,
    BeszelPage,
    BeszelSystems,
    BeszelSystemStats,
)
from varne.providers.types import RowDimSourceMeta


class BeszelService(ProviderService):
    client: BeszelClient

    def __init__(
        self,
        db: DatabaseBackend,
        client: BeszelClient,
        stack_id: StackId,
        source_id: SourceId,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        super().__init__(db, stack_id, source_id, lookback_days, now)
        self.client = client

    @property
    @override
    def provider(self) -> Literal[SourceType.BESZEL]:
        return SourceType.BESZEL

    def _fetch_systems(self) -> dict[str, str]:
        response = self.client.fetch_systems()
        raw = self._raw(response)
        self.store_raw([raw])

        systems = BeszelSystems.model_validate_json(response.text)
        return {system.id: system.name for system in systems.items}

    def _fetch_container_stats(
        self, interval: str, date_from: datetime
    ) -> list[BeszelContainerStats]:
        records: list[BeszelContainerStats] = []
        page = 1

        while True:
            response = self.client.fetch_container_stats(interval, date_from, page)
            self.store_raw([self._raw(response)])

            parsed = BeszelPage[BeszelContainerStats].model_validate_json(response.text)
            records += parsed.items

            if page >= parsed.total_pages:
                return records

            page += 1

    def _fetch_system_stats(
        self, interval: str, date_from: datetime
    ) -> list[BeszelSystemStats]:
        records: list[BeszelSystemStats] = []
        page = 1

        while True:
            response = self.client.fetch_system_stats(interval, date_from, page)
            self.store_raw([self._raw(response)])

            parsed = BeszelPage[BeszelSystemStats].model_validate_json(response.text)
            records += parsed.items

            if page >= parsed.total_pages:
                return records

            page += 1

    @override
    def fetch_source_meta(self) -> None:
        with self.pull():
            systems = self._fetch_systems()

            self.store_dim_source_meta(
                [
                    RowDimSourceMeta(
                        stack_id=self.stack_id,
                        source_id=self.source_id,
                        source_type=self.provider,
                        extracted_at=self._extracted_at(),
                        value_name="system",
                        value=name,
                    )
                    for name in systems.values()
                ]
            )

        logger.info(f"completed fetch source meta {self.provider}")

    @override
    def fetch_source_data(self) -> None:
        with self.pull():
            date_from, _ = self.period()
            systems = self._fetch_systems()

            containers: list[BeszelContainerStats] = []
            machines: list[BeszelSystemStats] = []
            for interval, _ in INTERVALS:
                containers += self._fetch_container_stats(interval, date_from)
                machines += self._fetch_system_stats(interval, date_from)

            self.store_fact_usage(
                transform_stats(
                    self.stack_id,
                    self.source_id,
                    self._extracted_at(),
                    containers,
                    machines,
                    systems,
                    date_from,
                )
            )

        logger.info(f"completed fetch source data {self.provider}")
