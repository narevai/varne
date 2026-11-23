from datetime import UTC, datetime, timedelta

from varne.providers.beszel.transform import transform_stats
from varne.providers.beszel.types import (
    BeszelContainer,
    BeszelContainerStats,
    BeszelSystemStats,
    BeszelSystemValues,
)
from varne.providers.docker.usage import HourlyUsage

MIB = 1024 * 1024
WINDOW_START = datetime(2026, 11, 19, tzinfo=UTC)


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 11, 19, hour, minute, tzinfo=UTC)


def record(
    interval: str, created: datetime, containers: dict[str, tuple[float, float]]
) -> BeszelContainerStats:
    return BeszelContainerStats(
        created=created,
        system="sys1",
        type=interval,
        stats=[BeszelContainer(n=n, c=c, m=m) for n, (c, m) in containers.items()],
    )


def minutes(start: datetime, count: int, cpu: float, memory: float):
    return [
        record("1m", start + timedelta(minutes=i + 1), {"web": (cpu, memory)})
        for i in range(count)
    ]


def transform(
    records: list[BeszelContainerStats], date_from: datetime = WINDOW_START
) -> dict[tuple[datetime, str], int]:
    rows: list[HourlyUsage] = transform_stats(records, [], {"sys1": "lab"}, date_from)
    return {
        (row.hour, f"{row.system}/{row.entity}/{row.metric}"): row.value for row in rows
    }


def test_hour_is_the_average_of_its_samples():
    records = minutes(at(10), 30, cpu=10, memory=100) + minutes(
        at(10, 30), 30, cpu=30, memory=300
    )

    usage = transform(records)

    assert usage[at(10), "lab/web/cpu"] == 2000
    assert usage[at(10), "lab/web/memory"] == 200 * MIB


def test_rows_are_named_by_system_container_and_metric():
    rows = transform_stats(minutes(at(10), 60, 1, 1), [], {"sys1": "lab"}, at(0))

    assert {(r.system, r.entity, r.metric) for r in rows} == {
        ("lab", "web", "cpu"),
        ("lab", "web", "memory"),
    }


def test_finer_samples_win_over_coarser_ones_for_the_same_time():
    records = [
        record("10m", at(10, 10), {"web": (50, 0)}),
        *[record("1m", at(10, 5 + i + 1), {"web": (10, 0)}) for i in range(5)],
    ]

    usage = transform(records)

    # 5 minutes from the 10m record (50) and 5 from the 1m records (10)
    assert usage[at(10), "lab/web/cpu"] == 3000


def test_container_missing_from_a_sample_counts_as_idle_then():
    records = [
        record("1m", at(10, 1), {"web": (40, 0), "db": (20, 0)}),
        record("1m", at(10, 2), {"web": (40, 0)}),
    ]

    usage = transform(records)

    assert usage[at(10), "lab/web/cpu"] == 4000
    assert usage[at(10), "lab/db/cpu"] == 1000


def test_coarse_sample_is_spread_over_every_hour_it_covers():
    usage = transform([record("120m", at(11), {"web": (20, 0)})])

    assert usage[at(9), "lab/web/cpu"] == 2000
    assert usage[at(10), "lab/web/cpu"] == 2000


def test_hours_before_the_window_are_dropped():
    usage = transform([record("120m", at(11), {"web": (20, 0)})], date_from=at(10))

    assert {hour for hour, _ in usage} == {at(10)}


def test_unknown_system_falls_back_to_its_id():
    rows = transform_stats(minutes(at(10), 1, 1, 1), [], {}, at(0))

    assert {r.system for r in rows} == {"sys1"}


def test_nothing_recorded_gives_no_rows():
    assert transform([]) == {}


def test_whole_machine_figures_are_stored_under_system():
    machine = BeszelSystemStats(
        created=at(10, 1),
        system="sys1",
        type="1m",
        stats=BeszelSystemValues(cpu=5.5, m=16, mu=2, du=10, la=[1.5, 2, 3]),
    )

    rows = transform_stats([], [machine], {"sys1": "lab"}, at(0))

    assert {(row.entity, row.metric): row.value for row in rows} == {
        ("system", "cpu"): 550,
        ("system", "memory"): 2 * 1024**3,
        ("system", "memory_total"): 16 * 1024**3,
        ("system", "disk"): 10 * 1024**3,
        ("system", "load"): 150,
    }


def test_machine_records_do_not_change_the_container_average():
    machine = BeszelSystemStats(
        created=at(10, 1),
        system="sys1",
        type="1m",
        stats=BeszelSystemValues(cpu=50, m=1, mu=1, du=1, la=[1]),
    )
    records = minutes(at(10), 1, cpu=10, memory=100)

    rows = transform_stats(records, [machine], {"sys1": "lab"}, at(0))

    usage = {f"{row.system}/{row.entity}/{row.metric}": row.value for row in rows}
    assert usage["lab/web/cpu"] == 1000
    assert usage["lab/system/cpu"] == 5000
