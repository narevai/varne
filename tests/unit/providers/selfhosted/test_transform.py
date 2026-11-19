from datetime import UTC, datetime
from decimal import Decimal

from varne.providers.selfhosted.rates import CostLine
from varne.providers.selfhosted.transform import hours_in_day, transform_costs

DAY = datetime(2026, 9, 9, tzinfo=UTC)
HOSTING = CostLine("Hosting", Decimal("0.5"), Decimal(1), "hours")
POWER = CostLine("Electricity", Decimal("0.03"), Decimal("0.1"), "kWh")


def rows(now: datetime, lines: list[CostLine], days: int = 3):
    return transform_costs(
        "stack",
        "source",
        now,
        lines,
        datetime(2026, 9, 8, tzinfo=UTC),
        datetime(2026, 9, 8 + days, tzinfo=UTC),
    )


def test_a_finished_day_is_24_hours_and_today_only_the_elapsed_part():
    now = datetime(2026, 9, 10, 6, 30, tzinfo=UTC)

    assert hours_in_day(DAY, now) == Decimal(24)
    assert hours_in_day(datetime(2026, 9, 10, tzinfo=UTC), now) == Decimal("6.5")
    assert hours_in_day(datetime(2026, 9, 11, tzinfo=UTC), now) == Decimal(0)


def test_every_day_gets_a_row_per_line_with_the_hours_of_that_day():
    result = rows(datetime(2026, 9, 10, 12, tzinfo=UTC), [HOSTING], days=3)

    assert [(r.charge_period_start.day, r.billed_cost) for r in result] == [
        (8, Decimal(12)),
        (9, Decimal(12)),
        (10, Decimal(6)),
    ]


def test_future_days_get_no_rows():
    result = rows(datetime(2026, 9, 9, 0, 0, tzinfo=UTC), [HOSTING], days=3)

    assert [r.charge_period_start.day for r in result] == [8]


def test_electricity_row_carries_kwh_and_usd():
    result = rows(datetime(2026, 9, 10, 0, 0, tzinfo=UTC), [POWER], days=1)

    row = result[0]
    assert row.billed_cost == Decimal("0.72")
    assert row.effective_cost == row.billed_cost
    assert row.billing_currency == "USD"
    assert row.pricing_currency == "USD"
    assert row.consumed_quantity == Decimal("2.4")
    assert row.consumed_unit == "kWh"
    assert row.service_name == "Electricity"
    assert row.service_provider_name == "Self-hosted"
    assert row.charge_period_end == datetime(2026, 9, 9, tzinfo=UTC)


def test_costs_that_do_not_fit_the_column_are_rounded():
    third = CostLine(
        "Hardware amortization", Decimal(1) / Decimal(3), Decimal(1), "hours"
    )

    result = rows(datetime(2026, 9, 10, tzinfo=UTC), [third], days=1)

    assert result[0].billed_cost == Decimal("8.000000000000000000")
