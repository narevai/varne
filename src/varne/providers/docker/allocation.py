import json
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timedelta
from decimal import Decimal

from varne.config import SourceId, SourceType, StackId
from varne.providers.docker.rates import CostLine
from varne.providers.docker.usage import (
    PERCENT_FACTOR,
    SYSTEM_ENTITY,
    DockerUsage,
    HourlyUsage,
)
from varne.providers.types import RowFactBilling

CURRENCY = "USD"
IDLE = "Idle"

HOUR = timedelta(hours=1)
DAY = timedelta(days=1)

# A container is charged for the share of the machine it used: half for the
# processor, half for the memory.
CPU_WEIGHT = Decimal("0.5")
MEMORY_WEIGHT = Decimal("0.5")
CPU_FULL = Decimal(100 * PERCENT_FACTOR)

type Container = tuple[str, str]
type Shares = dict[Container, Decimal]


def elapsed(hour: datetime, now: datetime) -> Decimal:
    """Part of the hour that has already happened."""
    if now >= hour + HOUR:
        return Decimal(1)

    if now <= hour:
        return Decimal(0)

    return Decimal(str((now - hour).total_seconds())) / Decimal(HOUR.total_seconds())


def shares_in_hour(usage: Sequence[HourlyUsage]) -> Shares:
    """Fraction of the machine's capacity each container used in the hour.

    Capacity is the whole machine, or all the monitored machines together:
    100 % of the processor of each and all their memory. Without it nothing
    can be attributed, so the hour stays unallocated.
    """
    cpu_capacity = CPU_FULL * len(
        {u.system for u in usage if u.entity == SYSTEM_ENTITY and u.metric == "cpu"}
    )
    memory_capacity = Decimal(
        sum(
            u.value
            for u in usage
            if u.entity == SYSTEM_ENTITY and u.metric == "memory_total"
        )
    )

    if cpu_capacity == 0 or memory_capacity == 0:
        return {}

    shares: Shares = defaultdict(Decimal)
    for u in usage:
        if u.entity == SYSTEM_ENTITY:
            continue

        if u.metric == "cpu":
            shares[u.system, u.entity] += CPU_WEIGHT * Decimal(u.value) / cpu_capacity
        elif u.metric == "memory":
            shares[u.system, u.entity] += (
                MEMORY_WEIGHT * Decimal(u.value) / memory_capacity
            )

    total = sum(shares.values(), Decimal(0))
    if total > 1:
        return {container: share / total for container, share in shares.items()}

    return dict(shares)


def allocate_costs(
    stack_id: StackId,
    source_id: SourceId,
    extracted_at: datetime,
    usage: DockerUsage,
    lines: Sequence[CostLine],
    date_from: datetime,
    date_to: datetime,
) -> list[RowFactBilling]:
    """Split the machine's cost over its containers, an hour at a time.

    Every hour that has happened costs the machine the same, used or not. What
    the containers did not use is booked as `Idle`, so the rows of a day always
    add up to the cost of the machine. Nothing is booked before the first hour
    the monitoring has data for, as the machine's cost would show a month the
    app never watched.
    """
    cost_per_hour = sum((line.cost_per_hour for line in lines), Decimal(0))

    by_hour: dict[datetime, list[HourlyUsage]] = defaultdict(list)
    for item in usage.hours:
        by_hour[item.hour].append(item)

    costs: dict[tuple[datetime, Container | None], Decimal] = defaultdict(Decimal)
    hours: dict[tuple[datetime, Container | None], Decimal] = defaultdict(Decimal)

    if not by_hour:
        return []

    hour = max(date_from, min(by_hour))
    while hour < date_to:
        part = elapsed(hour, extracted_at)

        if part > 0:
            day = hour.replace(hour=0)
            shares = shares_in_hour(by_hour.get(hour, []))

            for container, share in shares.items():
                costs[day, container] += cost_per_hour * part * share
                hours[day, container] += part * share

            idle = 1 - sum(shares.values(), Decimal(0))
            costs[day, None] += cost_per_hour * part * idle
            hours[day, None] += part * idle

        hour += HOUR

    rows = [
        RowFactBilling(
            stack_id=stack_id,
            source_id=source_id,
            source_type=SourceType.DOCKER,
            extracted_at=extracted_at,
            charge_period_start=day,
            charge_period_end=day + DAY,
            charge_category="Usage",
            billed_cost=cost,
            billing_currency=CURRENCY,
            effective_cost=cost,
            service_name=IDLE if container is None else container[1],
            service_category="Compute",
            service_provider_name="Self-hosted",
            consumed_quantity=hours[day, container],
            consumed_unit="hours",
            tags=tags(container, usage.images),
            pricing_category="Standard",
            pricing_currency=CURRENCY,
            pricing_quantity=hours[day, container],
            pricing_unit="hours",
        )
        for (day, container), cost in costs.items()
        if cost > 0
    ]

    return sorted(rows, key=lambda row: (row.charge_period_start, row.service_name))


def tags(container: Container | None, images: dict[Container, str]) -> str:
    if container is None:
        return "{}"

    system, _ = container
    image = images.get(container)

    return json.dumps(
        {"system": system} if image is None else {"system": system, "image": image}
    )
