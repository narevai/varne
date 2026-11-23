import json
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import cast

from varne.catalog.images import Application, application_name, identify
from varne.providers.docker.allocation import IDLE

HOURS_PER_MONTH = Decimal(730)
HOURS_PER_DAY = Decimal(24)

# Containers whose image says nothing about the application.
OTHER = "Other"


@dataclass(frozen=True)
class ContainerCost:
    source_id: str
    name: str
    image: str | None
    cost: Decimal
    hours: Decimal


@dataclass(frozen=True)
class AppComparison:
    app: str
    icon: str | None
    # Names of the containers it runs in, the one that costs most first.
    containers: tuple[str, ...]
    # What running it costs in a month.
    self_hosted: Decimal
    # The subscription it stands in for, when there is one.
    alternative: str | None
    # What that subscription would cost in a month, and so is not paid by running
    # the application oneself.
    avoided_cost: Decimal | None


@dataclass(frozen=True)
class Comparison:
    apps: list[AppComparison]
    # Everything the machines cost in a month: applications and idle capacity.
    machine_cost: Decimal
    idle: Decimal
    avoided_cost: Decimal
    # How long the machines ran, which is the period everything above covers.
    hours: Decimal

    @property
    def days(self) -> Decimal:
        return self.hours / HOURS_PER_DAY

    @property
    def roi(self) -> Decimal | None:
        if self.machine_cost == 0:
            return None

        return (self.avoided_cost - self.machine_cost) / self.machine_cost


def image_of(tags: str) -> str | None:
    return cast(dict[str, str], json.loads(tags)).get("image")


def compare(costs: Iterable[ContainerCost]) -> Comparison:
    """What every application costs to run, and what it would cost as a subscription.

    The costs cover the days of data there are and are scaled to a month, so
    that they can be set against the price of a plan as it is on its page.

    The investment is the whole machine, not only the applications that have a
    subscription to compare with, so that idle capacity and the rest weigh on
    the return as they do in reality.
    """
    costs = list(costs)

    hours_per_source: dict[str, Decimal] = {}
    for item in costs:
        hours_per_source[item.source_id] = (
            hours_per_source.get(item.source_id, Decimal(0)) + item.hours
        )
    # Machines run side by side, a subscription runs once.
    period_hours = max(hours_per_source.values(), default=Decimal(0))
    to_month = HOURS_PER_MONTH / period_hours if period_hours > 0 else Decimal(0)

    idle = Decimal(0)
    self_hosted: dict[str, Decimal] = {}
    containers: dict[str, dict[str, Decimal]] = {}
    found: dict[str, Application] = {}
    for item in costs:
        if item.name == IDLE:
            idle += item.cost * to_month
            continue

        app = identify(item.image) or Application(OTHER, None)
        self_hosted[app.name] = (
            self_hosted.get(app.name, Decimal(0)) + item.cost * to_month
        )
        per_container = containers.setdefault(app.name, {})
        per_container[item.name] = per_container.get(item.name, Decimal(0)) + item.cost
        found[app.name] = app

    apps = [
        AppComparison(
            name,
            app.icon,
            tuple(
                container
                for container, _ in sorted(
                    containers[name].items(), key=lambda c: (-c[1], c[0])
                )
            ),
            self_hosted[name],
            app.alternative,
            app.usd_per_month,
        )
        for name, app in found.items()
    ]
    apps.sort(key=lambda app: app.self_hosted, reverse=True)

    return Comparison(
        apps=apps,
        machine_cost=sum((item.cost for item in costs), Decimal(0)) * to_month,
        idle=idle,
        # One subscription stands in for all the applications it replaces.
        avoided_cost=sum(
            {
                app.alternative: app.avoided_cost
                for app in apps
                if app.alternative is not None and app.avoided_cost is not None
            }.values(),
            Decimal(0),
        ),
        hours=period_hours,
    )


def application_of(name: str, image: str | None) -> str:
    """The application a container belongs to, or `Idle` for unused capacity."""
    if name == IDLE:
        return IDLE

    return application_name(image) or OTHER
