"""Pulling the same period twice must replace it, not add to it."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast, override

import pandas as pd

from varne.config import SourceType
from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService
from varne.providers.types import RowDimSourceMeta, RowFactBilling, RowFactUsage

T0 = datetime(2026, 9, 10, 8, 0, tzinfo=UTC)
T1 = T0 + timedelta(hours=1)


def day(n: int) -> datetime:
    return datetime(2026, 9, n, tzinfo=UTC)


class FakeService(ProviderService):
    @property
    @override
    def provider(self) -> str:
        return "fake"

    @override
    def fetch_source_meta(self) -> None:
        pass

    @override
    def fetch_source_data(self) -> None:
        pass


def billing(source_id: str, d: int, at: datetime, cost: str = "1") -> RowFactBilling:
    return RowFactBilling(
        stack_id="stack",
        source_id=source_id,
        source_type=SourceType.VERCEL,
        extracted_at=at,
        charge_period_start=day(d),
        charge_period_end=day(d + 1),
        charge_category="Usage",
        billed_cost=Decimal(cost),
        billing_currency="USD",
        effective_cost=Decimal(cost),
        service_name="svc",
        service_category="cat",
        service_provider_name="Vercel",
        consumed_quantity=Decimal(1),
        consumed_unit="x",
        tags="{}",
        pricing_category="p",
        pricing_currency="USD",
        pricing_quantity=Decimal(1),
        pricing_unit="x",
    )


def usage(source_id: str, d: int, at: datetime, name: str = "visitors") -> RowFactUsage:
    return RowFactUsage(
        stack_id="stack",
        source_id=source_id,
        source_type=SourceType.VERCEL,
        extracted_at=at,
        event_time=day(d),
        usage_name=name,
        usage=5,
    )


def count(db: DatabaseBackend, table: TableName) -> int:
    return cast(int, db.table(table).count().execute())


def billing_rows(db: DatabaseBackend, source_id: str) -> list[tuple[datetime, Decimal]]:
    df = cast(pd.DataFrame, db.table(TableName.FACT_BILLING).execute())
    df = cast(pd.DataFrame, df[df["source_id"] == source_id])
    starts = cast(list[datetime], df["charge_period_start"].tolist())
    costs = cast(list[Decimal], df["billed_cost"].tolist())
    return sorted(zip(starts, costs, strict=True))


def billed_days(db: DatabaseBackend, source_id: str) -> list[int]:
    return [start.day for start, _ in billing_rows(db, source_id)]


def test_pulling_the_same_period_twice_keeps_one_copy(db: DatabaseBackend):
    service = FakeService(db, "stack", "src")

    service.replace_fact_billing(
        [billing("src", 1, T0), billing("src", 2, T0)], day(1), day(3)
    )
    service.replace_fact_billing(
        [billing("src", 1, T1), billing("src", 2, T1)], day(1), day(3)
    )

    assert count(db, TableName.FACT_BILLING) == 2


def test_a_new_pull_replaces_only_its_own_slice(db: DatabaseBackend):
    service = FakeService(db, "stack", "src")
    service.replace_fact_billing(
        [billing("src", d, T0) for d in (1, 2, 3, 4)], day(1), day(5)
    )

    # a later pull that only covers days 3..4
    service.replace_fact_billing(
        [billing("src", 3, T1, "9"), billing("src", 4, T1, "9")], day(3), day(4)
    )

    assert billed_days(db, "src") == [1, 2, 3, 4]
    costs = [cost for _, cost in billing_rows(db, "src")]
    assert costs == [Decimal(1), Decimal(1), Decimal(9), Decimal(9)]


def test_a_day_that_disappeared_from_the_window_is_removed(db: DatabaseBackend):
    service = FakeService(db, "stack", "src")
    service.replace_fact_billing(
        [billing("src", 1, T0), billing("src", 2, T0), billing("src", 3, T0)],
        day(1),
        day(3),
    )

    service.replace_fact_billing(
        [billing("src", 1, T1), billing("src", 3, T1)], day(1), day(3)
    )

    assert billed_days(db, "src") == [1, 3]


def test_other_sources_are_never_touched(db: DatabaseBackend):
    FakeService(db, "stack", "other").replace_fact_billing(
        [billing("other", 1, T0)], day(1), day(2)
    )
    FakeService(db, "stack", "src").replace_fact_billing(
        [billing("src", 1, T1)], day(1), day(2)
    )

    assert billed_days(db, "other") == [1]
    assert billed_days(db, "src") == [1]


def test_an_empty_response_keeps_existing_data(db: DatabaseBackend):
    service = FakeService(db, "stack", "src")
    service.replace_fact_billing([billing("src", 1, T0)], day(1), day(2))

    service.replace_fact_billing([], day(1), day(2))

    assert count(db, TableName.FACT_BILLING) == 1


def test_usage_from_several_projects_is_replaced_together(db: DatabaseBackend):
    service = FakeService(db, "stack", "src")
    first = [usage("src", 1, T0), usage("src", 1, T0, "pageviews")]
    service.replace_fact_usage(first, day(1), day(2))

    # same pull, two projects: both batches arrive in one call
    both = [usage("src", 1, T1), usage("src", 1, T1), usage("src", 1, T1, "pageviews")]
    service.replace_fact_usage(both, day(1), day(2))

    assert count(db, TableName.FACT_USAGE) == 3


def test_source_meta_keeps_only_the_latest_snapshot(db: DatabaseBackend):
    service = FakeService(db, "stack", "src")

    def meta(at: datetime) -> RowDimSourceMeta:
        return RowDimSourceMeta(
            stack_id="stack",
            source_id="src",
            source_type=SourceType.VERCEL,
            extracted_at=at,
            value_name="id",
            value="prj",
        )

    service.replace_dim_source_meta([meta(T0), meta(T0)])
    service.replace_dim_source_meta([meta(T1)])

    assert count(db, TableName.DIM_SOURCE_META) == 1
