from abc import ABC, abstractmethod
from enum import StrEnum
from typing import override

import ibis
import ibis.expr.datatypes as dt

from varne.db.types import DatabaseBackend


class TableName(StrEnum):
    RAW = "raw"
    DIM_SOURCE_META = "dim_source_meta"
    FACT_BILLING = "fact_billing"
    FACT_USAGE = "fact_usage"


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


class TableFactBilling(Table):
    @property
    @override
    def name(self) -> TableName:
        return TableName.FACT_BILLING

    @property
    @override
    def schema(self) -> ibis.Schema:
        return ibis.schema(
            {
                "stack_id": dt.string,
                "source_id": dt.string,
                "source_type": dt.string,
                "extracted_at": dt.timestamp,
                "charge_period_start": dt.timestamp,
                "charge_period_end": dt.timestamp,
                "charge_category": dt.string,
                "billed_cost": dt.Decimal(precision=38, scale=18),
                "billing_currency": dt.string,
                "effective_cost": dt.Decimal(precision=38, scale=18),
                "service_name": dt.string,
                "service_category": dt.string,
                "service_provider_name": dt.string,
                "consumed_quantity": dt.Decimal(precision=38, scale=18),
                "consumed_unit": dt.string,
                "tags": dt.string,
                "pricing_category": dt.string,
                "pricing_currency": dt.string,
                "pricing_quantity": dt.Decimal(precision=38, scale=18),
                "pricing_unit": dt.string,
            }
        )


class TableFactUsage(Table):
    @property
    @override
    def name(self) -> TableName:
        return TableName.FACT_USAGE

    @property
    @override
    def schema(self) -> ibis.Schema:
        return ibis.schema(
            {
                "stack_id": dt.string,
                "source_id": dt.string,
                "source_type": dt.string,
                "extracted_at": dt.timestamp,
                "event_time": dt.timestamp,
                "usage_name": dt.string,
                "usage": dt.uint32,
            }
        )


TABLES: list[Table] = [
    TableRaw(),
    TableDimSourceMeta(),
    TableFactBilling(),
    TableFactUsage(),
]


def create_tables(db: DatabaseBackend) -> None:
    existing_tables = set(db.list_tables())

    for table in TABLES:
        if table.name not in existing_tables:
            db.create_table(table.name, schema=table.schema)
