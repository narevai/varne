from abc import ABC, abstractmethod

import httpx2 as httpx
from loguru import logger

from varne.config import SourceId, StackId
from varne.db.schema import TableDimSourceMeta, TableRaw
from varne.db.types import DatabaseBackend
from varne.providers.types import RowRaw, RowStaging


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

    def __init__(
        self, db: DatabaseBackend, stack_id: StackId, source_id: SourceId
    ) -> None:
        self.db = db
        self.table_raw = TableRaw()
        self.table_dim_source_meta = TableDimSourceMeta()
        self.stack_id = stack_id
        self.source_id = source_id

    @property
    @abstractmethod
    def provider(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch_and_store(self) -> None:
        raise NotImplementedError()

    def store_raw(self, rows: list[RowRaw]):
        logger.debug(f"saving rows to {self.table_raw.name}")
        payload = [row.model_dump() for row in rows]
        self.db.insert(self.table_raw.name, payload)

    def store_staging(self, rows: list[RowStaging]):
        logger.debug(f"saving rows to {self.table_dim_source_meta.name}")
        payload = [row.model_dump() for row in rows]
        self.db.insert(self.table_dim_source_meta.name, payload)
