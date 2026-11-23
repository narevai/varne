from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import httpx2 as httpx

# Whole-machine figures live under this stand-in for a container name.
SYSTEM_ENTITY = "system"

# CPU is stored as a percentage times this factor, so 100 % is 10_000.
PERCENT_FACTOR = 100

type RecordResponse = Callable[[httpx.Response], None]


@dataclass(frozen=True)
class HourlyUsage:
    """Average of one metric of one container (or the machine) in one hour."""

    hour: datetime
    system: str
    entity: str
    metric: str
    value: int


@dataclass(frozen=True)
class DockerUsage:
    hours: list[HourlyUsage]
    # (system, container) -> image the container was started from
    images: dict[tuple[str, str], str]


class UsageSource(Protocol):
    """Where the per-container usage of a Docker host comes from."""

    def systems(self, record: RecordResponse, /) -> list[str]: ...

    def fetch(self, date_from: datetime, record: RecordResponse, /) -> DockerUsage: ...
