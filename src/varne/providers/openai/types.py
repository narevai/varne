from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from varne.providers.types import Amount


class OpenAICostAmount(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    value: Amount
    currency: str


class OpenAICostResult(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    amount: OpenAICostAmount | None = None
    line_item: str | None = None
    project_id: str | None = None
    quantity: Amount | None = None
    quantity_unit: str | None = None


class OpenAICostBucket(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    start_time: datetime
    end_time: datetime
    results: list[OpenAICostResult]


class OpenAICostsPage(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    data: list[OpenAICostBucket]
    has_more: bool
    next_page: str | None = None
