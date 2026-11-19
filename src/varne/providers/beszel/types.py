from datetime import datetime, timedelta
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

# Beszel keeps the same series at several resolutions, finest first.
# A record is stamped with the end of the period it summarises.
INTERVALS: tuple[tuple[str, timedelta], ...] = (
    ("1m", timedelta(minutes=1)),
    ("10m", timedelta(minutes=10)),
    ("20m", timedelta(minutes=20)),
    ("120m", timedelta(minutes=120)),
    ("480m", timedelta(minutes=480)),
)


class BeszelAuth(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    token: str


class BeszelSystem(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    id: str
    name: str


class BeszelSystems(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    items: list[BeszelSystem]


class BeszelContainer(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    n: str
    c: float = Field(ge=0)
    m: float = Field(ge=0)


class BeszelContainerStats(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    created: datetime
    system: str
    type: str
    stats: list[BeszelContainer]


class BeszelSystemValues(BaseModel):
    """Whole-machine figures; memory and disk are in GiB, `la` is the load average."""

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    cpu: float = Field(ge=0)
    mu: float = Field(ge=0)
    du: float = Field(ge=0)
    la: list[float] = Field(min_length=1)


class BeszelSystemStats(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    created: datetime
    system: str
    type: str
    stats: BeszelSystemValues


class BeszelPage[T](BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="ignore", populate_by_name=True
    )

    total_pages: int = Field(alias="totalPages")
    items: list[T]
