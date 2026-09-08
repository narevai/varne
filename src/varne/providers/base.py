from abc import ABC, abstractmethod

import httpx2 as httpx
from loguru import logger

from varne.config import SourceId, StackId
from varne.db.schema import TableRaw, TableStaging
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
    def base_url(self) -> str:
        raise NotImplementedError()


class ProviderService(ABC):
    db: DatabaseBackend
    stack_id: StackId
    source_id: SourceId
    raw_table: TableRaw
    staging_table: TableStaging

    def __init__(
        self, db: DatabaseBackend, stack_id: StackId, source_id: SourceId
    ) -> None:
        self.db = db
        self.raw_table = TableRaw()
        self.staging_table = TableStaging()
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
        logger.debug(f"saving rows to {self.raw_table.name}")
        payload = [row.model_dump() for row in rows]
        self.db.insert(self.raw_table.name, payload)

    def store_staging(self, rows: list[RowStaging]):
        logger.debug(f"saving rows to {self.staging_table.name}")
        payload = [row.model_dump() for row in rows]
        self.db.insert(self.staging_table.name, payload)
