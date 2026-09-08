from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from varne.config import SourceId, StackId


class RowRaw(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", strict=True)

    stack_id: StackId
    source_id: SourceId
    provider: str
    event_time: datetime
    payload: str


class RowStaging(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", strict=True)

    stack_id: StackId
    source_id: SourceId
    provider: str
    id: str
    event_time: datetime
    amount: float
