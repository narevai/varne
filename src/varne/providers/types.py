from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class RowRaw(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", strict=True)

    provider: str
    event_time: datetime
    payload: str


class RowStaging(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", strict=True)

    id: str
    event_time: datetime
    amount: float
