from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from varne.providers.types import Amount


def camel_to_pascal(value: str) -> str:
    return "".join(part.capitalize() for part in value.split("_"))


type TagValue = str | int | float | bool | None


class VercelProject(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    id: str
    name: str
    account_id: str = Field(alias="accountId")


class VercelProjectsResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    projects: list[VercelProject]


class VercelBilling(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="ignore", alias_generator=camel_to_pascal, populate_by_name=True
    )

    charge_period_start: datetime
    charge_period_end: datetime
    charge_category: str
    billed_cost: Amount
    billing_currency: str
    effective_cost: Amount
    service_name: str
    service_category: str
    service_provider_name: str
    consumed_quantity: Amount | None
    consumed_unit: str | None
    tags: dict[str, TagValue]
    pricing_category: str
    pricing_currency: str
    pricing_quantity: Amount
    pricing_unit: str


type VercelBillingResponse = list[VercelBilling]


class VercelWebAnalyticsQuery(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    since: datetime
    until: datetime
    limit: int


class VercelWebAnalyticsDataPoint(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    timestamp: datetime
    visitors: int
    pageviews: int


class VercelWebAnalyticsAggregateItem(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    version: int
    query: VercelWebAnalyticsQuery
    data: list[VercelWebAnalyticsDataPoint]


type VercelWebAnalyticsAggregateResponse = list[VercelWebAnalyticsAggregateItem]
