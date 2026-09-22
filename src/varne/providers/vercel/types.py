from datetime import datetime
from decimal import Decimal
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, RootModel


class VercelProject(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    id: str
    name: str
    account_id: str = Field(alias="accountId")


class VercelProjectsResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    projects: list[VercelProject]


class VercelBilling(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    charge_period_start: datetime
    charge_period_end: datetime
    charge_category: str
    billed_cost: Decimal = Field(max_digits=20, decimal_places=18)
    billing_currency: str
    effective_cost: Decimal = Field(max_digits=20, decimal_places=18)
    service_name: str
    service_category: str
    service_provider_name: str
    consumed_quantity: str
    consumed_unit: str
    tags: str
    pricing_category: str
    pricing_currency: str
    pricing_quantity: Decimal = Field(max_digits=20, decimal_places=18)
    pricing_unit: str


class VercelBillingResponse(RootModel[list[VercelBilling]]):
    pass


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


class VercelWebAnalyticsAggregateResponse(
    RootModel[list[VercelWebAnalyticsAggregateItem]]
):
    pass
