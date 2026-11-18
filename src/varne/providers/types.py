from datetime import datetime
from decimal import Decimal, localcontext
from typing import Annotated, ClassVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from varne.config import SourceId, SourceType, StackId

DECIMAL_SCALE = 18


def round_amount(value: object) -> object:
    if not isinstance(value, float):
        return value

    with localcontext() as context:
        context.prec = 38
        return Decimal(str(value)).quantize(Decimal(1).scaleb(-DECIMAL_SCALE))


type Amount = Annotated[
    Decimal,
    BeforeValidator(round_amount),
    Field(max_digits=38, decimal_places=DECIMAL_SCALE),
]


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
    billed_cost: Amount
    billing_currency: str
    effective_cost: Amount
    service_name: str
    service_category: str
    service_provider_name: str
    consumed_quantity: Amount | None
    consumed_unit: str | None
    tags: str
    pricing_category: str
    pricing_currency: str
    pricing_quantity: Amount
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
