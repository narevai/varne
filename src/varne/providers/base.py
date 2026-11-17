from abc import ABC, abstractmethod
from datetime import UTC, datetime

import httpx2 as httpx
from loguru import logger

from varne.config import SourceId, StackId
from varne.db.lock import serialized
from varne.db.schema import (
    TableDimSourceMeta,
    TableFactBilling,
    TableFactUsage,
    TableName,
    TableRaw,
)
from varne.db.types import DatabaseBackend
from varne.providers.types import (
    RowDimSourceMeta,
    RowFactBilling,
    RowFactUsage,
    RowRaw,
)


class ProviderClient(ABC):
    http: httpx.Client

    def __init__(
        self,
        http: httpx.Client,
    ) -> None:
        self.http = http

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

    def __init__(
        self, db: DatabaseBackend, stack_id: StackId, source_id: SourceId
    ) -> None:
        self.db = db
        self.table_raw = TableRaw()
        self.table_dim_source_meta = TableDimSourceMeta()
        self.table_fact_billing = TableFactBilling()
        self.table_fact_usage = TableFactUsage()
        self.stack_id = stack_id
        self.source_id = source_id

    @property
    @abstractmethod
    def provider(self) -> str:
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
        logger.debug(f"saving rows to {self.table_dim_source_meta.name}")
        payload = [row.model_dump() for row in rows]
        self.db.insert(self.table_dim_source_meta.name, payload)

    @serialized
    def store_fact_billing(self, rows: list[RowFactBilling]):
        logger.debug(f"saving rows to {self.table_fact_billing.name}")
        payload = [row.model_dump() for row in rows]
        self.db.insert(self.table_fact_billing.name, payload)

    @serialized
    def store_fact_usage(self, rows: list[RowFactUsage]):
        logger.debug(f"saving rows to {self.table_fact_usage.name}")
        payload = [row.model_dump() for row in rows]
        self.db.insert(self.table_fact_usage.name, payload)

    @serialized
    def _delete_older(
        self,
        table: TableName,
        extracted_at: datetime,
        column: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> None:
        sql = (
            f"DELETE FROM {table.value} "
            "WHERE stack_id = ? AND source_id = ? AND extracted_at < ?"
        )
        params: list[object] = [
            self.stack_id,
            self.source_id,
            _utc_naive(extracted_at),
        ]
        if column is not None and start is not None and end is not None:
            sql += f" AND {column} >= ? AND {column} <= ?"
            params += [_utc_naive(start), _utc_naive(end)]
        self.db.con.execute(sql, params)

    @serialized
    def replace_dim_source_meta(self, rows: list[RowDimSourceMeta]) -> None:
        if not rows:
            return
        self.store_dim_source_meta(rows)
        self._delete_older(TableName.DIM_SOURCE_META, rows[0].extracted_at)

    @serialized
    def replace_fact_billing(
        self, rows: list[RowFactBilling], start: datetime, end: datetime
    ) -> None:
        if not rows:
            logger.warning("no billing rows returned, keeping existing data")
            return
        starts = [r.charge_period_start for r in rows]
        self.store_fact_billing(rows)
        self._delete_older(
            TableName.FACT_BILLING,
            rows[0].extracted_at,
            "charge_period_start",
            min(start, *starts),
            max(end, *starts),
        )

    @serialized
    def replace_fact_usage(
        self, rows: list[RowFactUsage], start: datetime, end: datetime
    ) -> None:
        if not rows:
            logger.warning("no usage rows returned, keeping existing data")
            return
        times = [r.event_time for r in rows]
        self.store_fact_usage(rows)
        self._delete_older(
            TableName.FACT_USAGE,
            rows[0].extracted_at,
            "event_time",
            min(start, *times),
            max(end, *times),
        )


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)
