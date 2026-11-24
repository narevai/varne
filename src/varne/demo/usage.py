import math
import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from varne.demo import MEMORY_GIB
from varne.providers.base import utc_now
from varne.providers.docker.usage import (
    PERCENT_FACTOR,
    SYSTEM_ENTITY,
    DockerUsage,
    HourlyUsage,
    RecordResponse,
)

MIB = 1024**2
GIB = 1024**3

SYSTEM = "demo-server"


@dataclass(frozen=True)
class Container:
    name: str
    image: str
    # Average use of the processor, in percent of the machine, and of the memory, in MiB.
    cpu: float
    memory: float
    # How much busier (or quieter) it is at the weekend.
    weekend: float


# Eleven of them stand in for a subscription, two do not. None of them is an
# application whose plan costs so much that it dwarfs the rest.
CONTAINERS: tuple[Container, ...] = (
    Container(
        "homelab-open-webui-1", "ghcr.io/open-webui/open-webui:v0.11.4", 10, 2800, 0.7
    ),
    Container("homelab-grafana-1", "grafana/grafana:latest", 3, 900, 0.5),
    Container(
        "homelab-healthchecks-1",
        "lscr.io/linuxserver/healthchecks:latest",
        2.5,
        500,
        0.9,
    ),
    Container(
        "homelab-immich-db-1",
        "ghcr.io/immich-app/postgres:14-vectorchord0.4.3-pgvectors0.2.0",
        5,
        1500,
        1.6,
    ),
    Container(
        "homelab-stalwart-1", "ghcr.io/stalwartlabs/stalwart:v0.16.23", 1.5, 400, 0.6
    ),
    Container("homelab-searxng-1", "searxng/searxng:latest", 3, 600, 0.8),
    Container("homelab-logseq-1", "ghcr.io/logseq/logseq-webapp:latest", 1, 350, 1.1),
    Container(
        "homelab-netbird-client-1", "ghcr.io/netbirdio/netbird:0.79.0", 1.5, 200, 1.0
    ),
    Container(
        "homelab-windmill-lsp-1",
        "ghcr.io/windmill-labs/windmill-lsp:1.603.4",
        4,
        1200,
        0.4,
    ),
    Container(
        "homelab-homeassistant-1",
        "ghcr.io/home-assistant/home-assistant:stable",
        6,
        1800,
        1.3,
    ),
    Container(
        "homelab-mealie-1", "ghcr.io/mealie-recipes/mealie:latest", 2.5, 600, 1.8
    ),
    Container(
        "homelab-copyparty-1", "ghcr.io/9001/copyparty-ac:1.20.24", 2.5, 900, 1.4
    ),
    Container(
        "homelab-byb-budget-1", "ghcr.io/johnrbrady/byb-budget:1.0.0", 1.5, 300, 1.2
    ),
)


def jitter(key: str, spread: float) -> float:
    """A steady multiplier around 1: the same for the same key, every time."""
    return 1 + spread * (random.Random(key).random() - 0.5) * 2


def busy(container: Container, day: datetime) -> float:
    """How busy a container is on a day: it drifts, now and then it spikes, and at the
    weekend it does what it does at the weekend."""
    generator = random.Random(f"{container.name}:{day.date().isoformat()}")
    factor = 0.65 + 0.7 * generator.random()
    if generator.random() < 0.1:
        factor *= 1.8
    if day.weekday() >= 5:
        factor *= container.weekend
    return factor


def rhythm(hour: datetime) -> float:
    """More work in the day than in the night."""
    return 1 + 0.45 * math.sin((hour.hour - 9) / 24 * 2 * math.pi)


class DemoUsage:
    """A made up Docker host, so that the demo needs no machine and no hub.

    It answers like a source of usage does, and so goes through the same split of the
    cost as a real one. The numbers are the same for the same day, every time.
    """

    def __init__(self, now: Callable[[], datetime] = utc_now) -> None:
        self.now: Callable[[], datetime] = now

    def systems(self, _record: RecordResponse, /) -> list[str]:
        return [SYSTEM]

    def fetch(self, date_from: datetime, _record: RecordResponse, /) -> DockerUsage:
        end = self.now()
        hours: list[HourlyUsage] = []

        hour = date_from.replace(minute=0, second=0, microsecond=0)
        while hour <= end:
            used = 0
            for container in CONTAINERS:
                work = busy(container, hour) * rhythm(hour)
                key = f"{container.name}:{hour.isoformat()}"
                cpu = int(
                    container.cpu * work * jitter(f"{key}:cpu", 0.15) * PERCENT_FACTOR
                )
                memory = int(
                    container.memory
                    * (0.85 + 0.15 * busy(container, hour))
                    * jitter(f"{key}:memory", 0.03)
                    * MIB
                )
                used += memory
                hours.append(HourlyUsage(hour, SYSTEM, container.name, "cpu", cpu))
                hours.append(
                    HourlyUsage(hour, SYSTEM, container.name, "memory", memory)
                )

            hours += [
                HourlyUsage(hour, SYSTEM, SYSTEM_ENTITY, "cpu", 50 * PERCENT_FACTOR),
                HourlyUsage(hour, SYSTEM, SYSTEM_ENTITY, "memory", used),
                HourlyUsage(
                    hour, SYSTEM, SYSTEM_ENTITY, "memory_total", MEMORY_GIB * GIB
                ),
            ]
            hour += timedelta(hours=1)

        return DockerUsage(
            hours=hours,
            images={
                (SYSTEM, container.name): container.image for container in CONTAINERS
            },
        )
