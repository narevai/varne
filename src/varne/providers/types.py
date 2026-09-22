from datetime import datetime
from decimal import Decimal
from typing import Annotated, ClassVar

from pydantic import BaseModel, ConfigDict, Field

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


class RowFactBilling(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", strict=True)

    stack_id: StackId
    source_id: SourceId
    source_type: SourceType
    extracted_at: datetime
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


class RowFactUsage(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", strict=True)

    stack_id: StackId
    source_id: SourceId
    source_type: SourceType
    extracted_at: datetime
    event_time: datetime
    usage_name: str
    usage: Annotated[int, Field(ge=0)]
