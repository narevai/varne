from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Literal, override

import httpx2 as httpx
from loguru import logger

from varne.config import DEFAULT_LOOKBACK_DAYS, SourceId, SourceType, StackId
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService, utc_now
from varne.providers.vercel.client import VercelClient
from varne.providers.vercel.transform import (
    transform_analytics_aggregate,
    transform_billing,
    transform_meta,
)


class VercelService(ProviderService):
    client: VercelClient
    team_id: str
    project_ids: list[str]

    def __init__(
        self,
        db: DatabaseBackend,
        client: VercelClient,
        stack_id: StackId,
        source_id: SourceId,
        team_id: str,
        project_ids: Sequence[str] = (),
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        super().__init__(db, stack_id, source_id, lookback_days, now)
        self.client = client
        self.team_id = team_id
        self.project_ids = list(project_ids)

    @property
    @override
    def provider(self) -> Literal[SourceType.VERCEL]:
        return SourceType.VERCEL

    @override
    def fetch_source_meta(self) -> None:
        with self.pull():
            response: httpx.Response = self.client.fetch_projects()

            raw = self._raw(response)
            self.store_raw([raw])

            meta = transform_meta(raw)
            self.store_dim_source_meta(meta)
        logger.info(f"completed fetch source meta {self.provider}")

    @override
    def fetch_source_data(self) -> None:
        with self.pull():
            self._fetch_source_billing()
            self._fetch_source_usage()

        logger.info(f"completed fetch source data {self.provider}")

    def _fetch_source_billing(self) -> None:
        date_from, date_to = self.period()

        response: httpx.Response = self.client.fetch_billing(
            team_id=self.team_id, date_from=date_from, date_to=date_to
        )

        raw = self._raw(response)
        self.store_raw([raw])

        billing = transform_billing(raw)
        self.store_fact_billing(billing)

    def _fetch_source_usage(self) -> None:
        if not self.project_ids:
            logger.info("no project_ids configured, skipping web analytics")
            return

        date_from, date_to = self.period()

        for project_id in self.project_ids:
            response: httpx.Response = self.client.fetch_web_analytics_visits_aggregate(
                team_id=self.team_id,
                project_id=project_id,
                date_from=date_from,
                date_to=date_to,
            )

            raw = self._raw(response)
            self.store_raw([raw])

            usage = transform_analytics_aggregate(raw)
            self.store_fact_usage(usage)
