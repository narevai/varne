from abc import ABC, abstractmethod
from typing import override

import ibis
import ibis.expr.datatypes as dt

from varne.db.types import DatabaseBackend


class Table(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def schema(self) -> ibis.Schema:
        raise NotImplementedError()


class TableRaw(Table):
    @property
    @override
    def name(self):
        return "raw"

    @property
    @override
    def schema(self) -> ibis.Schema:
        return ibis.schema(
            {"provider": dt.string, "event_time": dt.timestamp, "payload": dt.string}
        )


class TableStaging(Table):
    @property
    @override
    def name(self) -> str:
        return "staging"

    @property
    @override
    def schema(self) -> ibis.Schema:
        return ibis.schema(
            {"id": dt.string, "event_time": dt.timestamp, "amount": dt.float}
        )


TABLES: list[Table] = [TableRaw(), TableStaging()]


def create_tables(db: DatabaseBackend) -> None:
    existing_tables = set(db.list_tables())

    for table in TABLES:
        if table.name not in existing_tables:
            db.create_table(table.name, schema=table.schema)
