from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from varne.providers.beszel.types import (
    INTERVALS,
    BeszelContainerStats,
    BeszelSystemStats,
)
from varne.providers.docker.usage import PERCENT_FACTOR, SYSTEM_ENTITY, HourlyUsage

# Beszel reports container memory in MiB and whole-machine memory/disk in GiB.
MIB = 1024**2
GIB = 1024**3

type Period = tuple[datetime, datetime]
type Values = dict[tuple[str, str], float]


@dataclass(frozen=True)
class Sample:
    """One Beszel record reduced to `(entity, metric) -> value` in stored units."""

    created: datetime
    system: str
    type: str
    values: Values


@dataclass(frozen=True)
class Segment:
    start: datetime
    end: datetime
    values: Values


def container_sample(record: BeszelContainerStats) -> Sample:
    values: Values = {}

    for container in record.stats:
        values[container.n, "cpu"] = container.c * PERCENT_FACTOR
        values[container.n, "memory"] = container.m * MIB

    return Sample(record.created, record.system, record.type, values)


def system_sample(record: BeszelSystemStats) -> Sample:
    stats = record.stats

    return Sample(
        record.created,
        record.system,
        record.type,
        {
            (SYSTEM_ENTITY, "cpu"): stats.cpu * PERCENT_FACTOR,
            (SYSTEM_ENTITY, "memory"): stats.mu * GIB,
            (SYSTEM_ENTITY, "memory_total"): stats.m * GIB,
            (SYSTEM_ENTITY, "disk"): stats.du * GIB,
            (SYSTEM_ENTITY, "load"): stats.la[0] * PERCENT_FACTOR,
        },
    )


def merge(periods: Sequence[Period]) -> list[Period]:
    merged: list[Period] = []

    for start, end in sorted(periods):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged


def uncovered(
    start: datetime, end: datetime, covered: Sequence[Period]
) -> list[Period]:
    free: list[Period] = []
    cursor = start

    for covered_start, covered_end in covered:
        if covered_end <= cursor or covered_start >= end:
            continue

        if covered_start > cursor:
            free.append((cursor, covered_start))

        cursor = max(cursor, covered_end)

    if cursor < end:
        free.append((cursor, end))

    return free


def segments_of(samples: Sequence[Sample]) -> list[Segment]:
    """Every moment is described by the finest resolution that has it."""
    segments: list[Segment] = []
    covered: list[Period] = []

    for interval, step in INTERVALS:
        taken = [sample for sample in samples if sample.type == interval]

        for sample in taken:
            for start, end in uncovered(sample.created - step, sample.created, covered):
                segments.append(Segment(start, end, sample.values))

        covered = merge(
            [*covered, *((sample.created - step, sample.created) for sample in taken)]
        )

    return segments


def hour_overlaps(segment: Segment) -> Iterator[tuple[datetime, float]]:
    hour = segment.start.replace(minute=0, second=0, microsecond=0)

    while hour < segment.end:
        overlap = min(segment.end, hour + timedelta(hours=1)) - max(segment.start, hour)
        yield hour, overlap.total_seconds()
        hour += timedelta(hours=1)


def hourly_usage(
    samples: Sequence[Sample],
    systems: Mapping[str, str],
    date_from: datetime,
) -> list[HourlyUsage]:
    rows: list[HourlyUsage] = []

    for system_id in sorted({sample.system for sample in samples}):
        observed: dict[datetime, float] = defaultdict(float)
        sums: dict[tuple[datetime, str, str], float] = defaultdict(float)

        for segment in segments_of([s for s in samples if s.system == system_id]):
            for hour, seconds in hour_overlaps(segment):
                if hour < date_from:
                    continue

                observed[hour] += seconds

                for (entity, metric), value in segment.values.items():
                    sums[hour, entity, metric] += value * seconds

        name = systems.get(system_id, system_id)

        rows.extend(
            HourlyUsage(
                hour=hour,
                system=name,
                entity=entity,
                metric=metric,
                value=round(total / observed[hour]),
            )
            for (hour, entity, metric), total in sorted(sums.items())
        )

    return rows


def transform_stats(
    containers: Sequence[BeszelContainerStats],
    machines: Sequence[BeszelSystemStats],
    systems: Mapping[str, str],
    date_from: datetime,
) -> list[HourlyUsage]:
    """Average usage in every hour, per system, container and metric.

    The average is taken over the time Beszel actually observed in that hour,
    so a container missing from a record counts as idle for that stretch.
    Containers and the whole machine come from different records, so each
    is averaged over its own observed time.
    """
    return [
        *hourly_usage(
            [container_sample(record) for record in containers], systems, date_from
        ),
        *hourly_usage(
            [system_sample(record) for record in machines], systems, date_from
        ),
    ]
