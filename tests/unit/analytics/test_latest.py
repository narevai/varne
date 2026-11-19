from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast

from varne.analytics.billing import get_billing_per_day, get_source_billing
from varne.analytics.cost_per_usage import get_source_cost_per_usage
from varne.analytics.usage import get_source_usage, get_usage_by_metric, get_usage_names
from varne.config import SourceType
from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.types import RowFactBilling, RowFactUsage

DAY1 = datetime(2026, 9, 1, tzinfo=UTC)
DAY2 = DAY1 + timedelta(days=1)
PULL1 = datetime(2026, 9, 2, 8, tzinfo=UTC)
PULL2 = datetime(2026, 9, 2, 20, tzinfo=UTC)


def billing(
    source_id: str, day: datetime, cost: str, pulled_at: datetime, service: str = "svc"
) -> RowFactBilling:
    return RowFactBilling(
        stack_id="stack",
        source_id=source_id,
        source_type=SourceType.VERCEL,
        extracted_at=pulled_at,
        charge_period_start=day,
        charge_period_end=day + timedelta(days=1),
        charge_category="Usage",
        billed_cost=Decimal(cost),
        billing_currency="USD",
        effective_cost=Decimal(cost),
        service_name=service,
        service_category="cat",
        service_provider_name="Vercel",
        consumed_quantity=None,
        consumed_unit=None,
        tags="{}",
        pricing_category="p",
        pricing_currency="USD",
        pricing_quantity=Decimal(1),
        pricing_unit="x",
    )


def usage(
    source_id: str,
    day: datetime,
    value: int,
    pulled_at: datetime,
    name: str = "visitors",
) -> RowFactUsage:
    return RowFactUsage(
        stack_id="stack",
        source_id=source_id,
        source_type=SourceType.VERCEL,
        extracted_at=pulled_at,
        event_time=day,
        usage_name=name,
        usage=value,
    )


def put_billing(db: DatabaseBackend, rows: list[RowFactBilling]) -> None:
    db.insert(TableName.FACT_BILLING, [row.model_dump() for row in rows])


def put_usage(db: DatabaseBackend, rows: list[RowFactUsage]) -> None:
    db.insert(TableName.FACT_USAGE, [row.model_dump() for row in rows])


def costs(db: DatabaseBackend) -> dict[str, Decimal]:
    df = get_source_billing(db, "stack", "a").to_pandas()
    days = cast(list[datetime], df["charge_period_start"].tolist())
    values = cast(list[Decimal], df["billed_cost"].tolist())

    return {str(day.date()): cost for day, cost in zip(days, values, strict=True)}


def test_a_later_pull_replaces_the_same_day_from_an_earlier_one(db: DatabaseBackend):
    put_billing(db, [billing("a", DAY1, "5", PULL1), billing("a", DAY1, "7", PULL2)])

    assert costs(db) == {"2026-09-01": Decimal("7")}


def test_days_only_in_an_older_pull_are_kept(db: DatabaseBackend):
    put_billing(
        db,
        [
            billing("a", DAY1, "5", PULL1),
            billing("a", DAY2, "6", PULL1),
            billing("a", DAY2, "9", PULL2),
        ],
    )

    assert costs(db) == {"2026-09-01": Decimal("5"), "2026-09-02": Decimal("9")}


def test_every_row_of_the_latest_pull_is_kept(db: DatabaseBackend):
    put_billing(
        db,
        [
            billing("a", DAY1, "1", PULL1, "x"),
            billing("a", DAY1, "2", PULL2, "x"),
            billing("a", DAY1, "3", PULL2, "y"),
        ],
    )

    df = get_source_billing(db, "stack", "a").to_pandas()
    names = cast(list[str], df["service_name"].tolist())
    values = cast(list[Decimal], df["billed_cost"].tolist())

    assert sorted(zip(names, values, strict=True)) == [
        ("x", Decimal("2")),
        ("y", Decimal("3")),
    ]


def test_sources_do_not_replace_each_other(db: DatabaseBackend):
    put_billing(db, [billing("a", DAY1, "5", PULL1), billing("b", DAY1, "8", PULL2)])

    assert costs(db) == {"2026-09-01": Decimal("5")}


def test_cost_per_day_counts_each_day_once(db: DatabaseBackend):
    put_billing(db, [billing("a", DAY1, "5", PULL1), billing("a", DAY1, "7", PULL2)])

    df = get_billing_per_day(db, "stack").to_pandas()

    assert cast(list[Decimal], df["cost"].tolist()) == [Decimal("7")]


def test_usage_comes_from_the_latest_pull_only(db: DatabaseBackend):
    put_usage(db, [usage("a", DAY1, 10, PULL1), usage("a", DAY1, 12, PULL2)])

    df = get_source_usage(db, "stack", "a").to_pandas()

    assert cast(list[int], df["usage"].tolist()) == [12]


def test_cost_per_visitor_uses_the_latest_pull_of_both(db: DatabaseBackend):
    put_billing(db, [billing("a", DAY1, "100", PULL1), billing("a", DAY1, "10", PULL2)])
    put_usage(db, [usage("a", DAY1, 50, PULL1), usage("a", DAY1, 5, PULL2)])

    df = get_source_cost_per_usage(db, "stack", "a").to_pandas()

    assert cast(list[float], df["cost_per_usage"].tolist()) == [2.0]


def test_usage_by_metric_keeps_only_that_metric_of_the_latest_pull(
    db: DatabaseBackend,
):
    put_usage(
        db,
        [
            usage("source", DAY1, 1, PULL1, "lab/web/cpu"),
            usage("source", DAY1, 2, PULL2, "lab/web/cpu"),
            usage("source", DAY1, 9, PULL2, "lab/web/memory"),
        ],
    )

    rows = get_usage_by_metric(db, "stack", "source", "cpu").to_pandas()
    names = get_usage_names(db, "stack", "source").to_pandas()

    assert rows["usage"].tolist() == [2]
    assert names["usage_name"].tolist() == ["lab/web/cpu", "lab/web/memory"]
