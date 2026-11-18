from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from varne.providers.types import Amount


class AnthropicCostResult(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    amount: Amount
    currency: str
    description: str | None = None
    cost_type: str | None = None
    model: str | None = None
    token_type: str | None = None
    service_tier: str | None = None
    context_window: str | None = None
    workspace_id: str | None = None


class AnthropicCostBucket(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    starting_at: datetime
    ending_at: datetime
    results: list[AnthropicCostResult]


class AnthropicCostReport(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    data: list[AnthropicCostBucket]
    has_more: bool
    next_page: str | None = None
