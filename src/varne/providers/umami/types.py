from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class UmamiDataPoint(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    x: datetime
    y: int = Field(ge=0)


class UmamiPageviews(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    pageviews: list[UmamiDataPoint]
    sessions: list[UmamiDataPoint]
