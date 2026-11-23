import json
from datetime import UTC, datetime
from decimal import Decimal

from varne.providers.docker.allocation import IDLE, allocate_costs, elapsed
from varne.providers.docker.rates import CostLine
from varne.providers.docker.usage import DockerUsage, HourlyUsage
from varne.providers.types import RowFactBilling

GIB = 1024**3
DAY = datetime(2026, 9, 9, tzinfo=UTC)
END = datetime(2026, 9, 11, tzinfo=UTC)
LINES = [CostLine("Hosting", Decimal(1), Decimal(1), "hours")]


def at(hour: int, day: int = 9) -> datetime:
    return datetime(2026, 9, day, hour, tzinfo=UTC)


def machine(hour: datetime, system: str = "lab", memory: int = 16) -> list[HourlyUsage]:
    return [
        HourlyUsage(hour, system, "system", "cpu", 5000),
        HourlyUsage(hour, system, "system", "memory_total", memory * GIB),
    ]


def container(
    hour: datetime, name: str, cpu: int, memory: int, system: str = "lab"
) -> list[HourlyUsage]:
    return [
        HourlyUsage(hour, system, name, "cpu", cpu),
        HourlyUsage(hour, system, name, "memory", memory * GIB),
    ]


def allocate(
    hours: list[HourlyUsage],
    now: datetime = END,
    images: dict[tuple[str, str], str] | None = None,
    lines: list[CostLine] | None = None,
) -> list[RowFactBilling]:
    return allocate_costs(
        "stack",
        "source",
        now,
        DockerUsage(hours, images or {}),
        lines or LINES,
        DAY,
        datetime(2026, 9, 12, tzinfo=UTC),
    )


def costs(rows: list[RowFactBilling]) -> dict[tuple[int, str], Decimal]:
    return {(r.charge_period_start.day, r.service_name): r.billed_cost for r in rows}


def test_a_container_pays_for_the_share_of_the_machine_it_used():
    # web uses 10 % of the processor and 25 % of the memory: 0.5 * 0.1 + 0.5 * 0.25
    hours = machine(at(10)) + container(at(10), "web", cpu=1000, memory=4)

    rows = allocate(hours, now=at(11))

    assert costs(rows)[9, "web"] == Decimal("0.175")
    # the rest of hour 10 and the ten hours before it, which have no usage
    assert costs(rows)[9, IDLE] == Decimal("10.825")


def test_rows_of_a_day_add_up_to_the_cost_of_the_machine():
    hours = (
        machine(at(10))
        + container(at(10), "web", 3000, 2)
        + container(at(10), "db", 1000, 8)
    )

    rows = allocate(hours, now=datetime(2026, 9, 10, tzinfo=UTC))

    assert sum(r.billed_cost for r in rows) == Decimal(24)


def test_hours_without_capacity_are_all_idle():
    hours = container(at(10), "web", 1000, 4)

    rows = allocate(hours, now=datetime(2026, 9, 10, tzinfo=UTC))

    assert costs(rows) == {(9, IDLE): Decimal(24)}


def test_a_container_cannot_use_more_than_the_machine_has():
    hours = (
        machine(at(10))
        + container(at(10), "web", 9000, 12)
        + container(at(10), "db", 9000, 12)
    )

    rows = allocate(hours, now=at(11))
    by_name = {name: cost for (_, name), cost in costs(rows).items()}

    assert by_name["web"] == by_name["db"]
    assert IDLE in by_name and by_name[IDLE] > 0
    assert sum(r.billed_cost for r in rows) == Decimal(11)


def test_a_part_played_hour_costs_only_the_part_that_has_happened():
    hours = machine(at(10)) + container(at(10), "web", 1000, 4)

    rows = allocate(hours, now=datetime(2026, 9, 9, 10, 30, tzinfo=UTC))

    assert costs(rows)[9, "web"] == Decimal("0.0875")
    assert sum(r.billed_cost for r in rows) == Decimal("10.5")


def test_future_hours_cost_nothing():
    rows = allocate([], now=datetime(2026, 9, 9, 6, 30, tzinfo=UTC))

    assert costs(rows) == {(9, IDLE): Decimal("6.5")}


def test_every_day_gets_its_own_rows():
    hours = (
        machine(at(10))
        + container(at(10), "web", 1000, 4)
        + machine(at(10, 10))
        + container(at(10, 10), "web", 1000, 4)
    )

    rows = allocate(hours, now=datetime(2026, 9, 11, tzinfo=UTC))

    assert {day for day, _ in costs(rows)} == {9, 10}
    assert costs(rows)[9, "web"] == costs(rows)[10, "web"]
    assert {r.charge_period_end.day for r in rows} == {10, 11}


def test_the_cost_of_all_lines_is_split_the_same_way():
    lines = [
        CostLine("Hardware amortization", Decimal("0.5"), Decimal(1), "hours"),
        CostLine("Electricity", Decimal("0.5"), Decimal("0.1"), "kWh"),
    ]
    hours = machine(at(10)) + container(at(10), "web", 1000, 4)

    rows = allocate(hours, now=at(11), lines=lines)

    assert costs(rows)[9, "web"] == Decimal("0.175")


def test_machines_are_pooled_into_one_capacity():
    # two machines of 16 GiB: 4 GiB is 12.5 %, 1000 of 20000 is 5 %
    hours = (
        machine(at(10), "a")
        + machine(at(10), "b")
        + container(at(10), "web", 1000, 4, system="a")
    )

    rows = allocate(hours, now=at(11))

    assert costs(rows)[9, "web"] == Decimal("0.0875")


def test_rows_carry_the_image_and_the_system_for_the_comparison():
    hours = (
        machine(at(10))
        + container(at(10), "web", 1000, 4)
        + container(at(10), "db", 1000, 4)
    )

    rows = allocate(hours, now=at(11), images={("lab", "web"): "nginx:1"})
    tags = {r.service_name: json.loads(r.tags) for r in rows}

    assert tags["web"] == {"system": "lab", "image": "nginx:1"}
    assert tags["db"] == {"system": "lab"}
    assert tags[IDLE] == {}


def test_rows_are_dollars_for_compute():
    rows = allocate(machine(at(10)) + container(at(10), "web", 1000, 4), now=at(11))

    row = next(r for r in rows if r.service_name == "web")
    assert row.billing_currency == "USD"
    assert row.pricing_currency == "USD"
    assert row.effective_cost == row.billed_cost
    assert row.service_category == "Compute"
    assert row.service_provider_name == "Self-hosted"
    assert row.consumed_unit == "hours"
    assert row.consumed_quantity == Decimal("0.175")


def test_hours_elapsed():
    now = datetime(2026, 9, 10, 6, 30, tzinfo=UTC)

    assert elapsed(datetime(2026, 9, 10, 5, tzinfo=UTC), now) == Decimal(1)
    assert elapsed(datetime(2026, 9, 10, 6, tzinfo=UTC), now) == Decimal("0.5")
    assert elapsed(datetime(2026, 9, 10, 7, tzinfo=UTC), now) == Decimal(0)
