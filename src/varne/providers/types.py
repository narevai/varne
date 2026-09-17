from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from varne.config import SourceId, SourceType, StackId


class RowRaw(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", strict=True)

    stack_id: StackId
    source_id: SourceId
    source_type: SourceType
    extracted_at: datetime
    method: str
    url: str
    payload: str


class RowDimSourceMeta(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", strict=True)

    stack_id: StackId
    source_id: SourceId
    source_type: SourceType
    extracted_at: datetime
    value_name: str
    value: str
