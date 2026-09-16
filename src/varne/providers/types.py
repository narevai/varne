from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from varne.config import SourceId, SourceType, StackId


class RowRaw(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", strict=True)

    stack_id: StackId
    source_id: SourceId
    source_type: SourceType
    method: str
    url: str
    extracted_at: datetime
    payload: str


class RowStaging(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", strict=True)

    stack_id: StackId
    source_id: SourceId
    provider: str
    id: str
    event_time: datetime
    amount: float
