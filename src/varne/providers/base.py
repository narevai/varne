from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import httpx2 as httpx
import pyarrow as pa
from loguru import logger

from varne.config import DEFAULT_LOOKBACK_DAYS, SourceId, SourceType, StackId
from varne.db.lock import serialized
from varne.db.schema import (
    TableDimSourceMeta,
    TableFactBilling,
    TableFactUsage,
    TableRaw,
)
from varne.db.types import DatabaseBackend
from varne.providers.types import (
    RowDimSourceMeta,
    RowFactBilling,
    RowFactUsage,
    RowRaw,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class ProviderClient(ABC):
    http: httpx.Client

    def __init__(
        self,
        http: httpx.Client,
    ) -> None:
        self.http = http

    @staticmethod
    def raise_for_status(response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as ex:
            raise httpx.HTTPStatusError(
                f"{ex} {response.text[:300]}", request=ex.request, response=response
            ) from ex

    @property
    @abstractmethod
    def base_url(self) -> httpx.URL:
        raise NotImplementedError()


class ProviderService(ABC):
    db: DatabaseBackend
    stack_id: StackId
    source_id: SourceId
    table_raw: TableRaw
    table_dim_source_meta: TableDimSourceMeta
    table_fact_billing: TableFactBilling
    table_fact_usage: TableFactUsage
    lookback_days: int
    _now: Callable[[], datetime]
    _pull_at: datetime | None

    def __init__(
        self,
        db: DatabaseBackend,
        stack_id: StackId,
        source_id: SourceId,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.db = db
        self.table_raw = TableRaw()
        self.table_dim_source_meta = TableDimSourceMeta()
        self.table_fact_billing = TableFactBilling()
        self.table_fact_usage = TableFactUsage()
        self.stack_id = stack_id
        self.source_id = source_id
        self.lookback_days = lookback_days
        self._now = now
        self._pull_at = None

    @contextmanager
    def pull(self) -> Generator[None]:
        self._pull_at = self._now()
        try:
            yield
        finally:
            self._pull_at = None

    def period(self) -> tuple[datetime, datetime]:
        today = (
            self._now()
            .astimezone(UTC)
            .replace(hour=0, minute=0, second=0, microsecond=0)
        )
        return today - timedelta(days=self.lookback_days), today + timedelta(days=1)

    def _raw(self, response: httpx.Response) -> RowRaw:
        return RowRaw(
            stack_id=self.stack_id,
            source_id=self.source_id,
            source_type=self.provider,
            extracted_at=self._pull_at or self._now(),
            method=response.request.method,
            url=str(response.request.url),
            payload=response.text,
        )

    @property
    @abstractmethod
    def provider(self) -> SourceType:
        raise NotImplementedError

    @abstractmethod
    def fetch_source_meta(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def fetch_source_data(self) -> None:
        raise NotImplementedError()

    @serialized
    def store_raw(self, rows: list[RowRaw]):
        logger.debug(f"saving rows to {self.table_raw.name}")
        payload = [row.model_dump() for row in rows]
        self.db.insert(self.table_raw.name, payload)

    @serialized
    def store_dim_source_meta(self, rows: list[RowDimSourceMeta]):
        if not rows:
            return

        logger.debug(f"saving rows to {self.table_dim_source_meta.name}")
        payload = [row.model_dump() for row in rows]
        self.db.insert(self.table_dim_source_meta.name, payload)

    @serialized
    def store_fact_billing(self, rows: list[RowFactBilling]):
        if not rows:
            return

        logger.debug(f"saving rows to {self.table_fact_billing.name}")
        payload = pa.Table.from_pylist(  # pyright: ignore[reportUnknownVariableType]
            [row.model_dump() for row in rows],
            schema=self.table_fact_billing.schema.to_pyarrow(),
        )
        self.db.insert(self.table_fact_billing.name, payload)  # pyright: ignore[reportUnknownArgumentType]

    @serialized
    def store_fact_usage(self, rows: list[RowFactUsage]):
        if not rows:
            return

        logger.debug(f"saving rows to {self.table_fact_usage.name}")
        payload = [row.model_dump() for row in rows]
        self.db.insert(self.table_fact_usage.name, payload)
