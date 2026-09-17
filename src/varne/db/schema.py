from abc import ABC, abstractmethod
from enum import StrEnum
from typing import override

import ibis
import ibis.expr.datatypes as dt

from varne.db.types import DatabaseBackend


class TableName(StrEnum):
    RAW = "raw"
    DIM_SOURCE_META = "dim_source_meta"


class Table(ABC):
    @property
    @abstractmethod
    def name(self) -> TableName:
        raise NotImplementedError()

    @property
    @abstractmethod
    def schema(self) -> ibis.Schema:
        raise NotImplementedError()


class TableRaw(Table):
    @property
    @override
    def name(self) -> TableName:
        return TableName.RAW

    @property
    @override
    def schema(self) -> ibis.Schema:
        return ibis.schema(
            {
                "stack_id": dt.string,
                "source_id": dt.string,
                "source_type": dt.string,
                "extracted_at": dt.timestamp,
                "method": dt.string,
                "url": dt.string,
                "payload": dt.string,
            }
        )


class TableDimSourceMeta(Table):
    @property
    @override
    def name(self) -> TableName:
        return TableName.DIM_SOURCE_META

    @property
    @override
    def schema(self) -> ibis.Schema:
        return ibis.schema(
            {
                "stack_id": dt.string,
                "source_id": dt.string,
                "source_type": dt.string,
                "extracted_at": dt.timestamp,
                "value_name": dt.string,
                "value": dt.string,
            }
        )


TABLES: list[Table] = [TableRaw(), TableDimSourceMeta()]


def create_tables(db: DatabaseBackend) -> None:
    existing_tables = set(db.list_tables())

    for table in TABLES:
        if table.name not in existing_tables:
            db.create_table(table.name, schema=table.schema)
