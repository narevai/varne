from datetime import datetime, timedelta
from decimal import Decimal

from varne.config import SourceId, SourceType, StackId
from varne.providers.selfhosted.rates import CostLine
from varne.providers.types import RowFactBilling

CURRENCY = "USD"
SECONDS_PER_HOUR = Decimal(3600)
HOURS_PER_DAY = Decimal(24)


def hours_in_day(day: datetime, now: datetime) -> Decimal:
    end = day + timedelta(days=1)

    if now >= end:
        return HOURS_PER_DAY

    if now <= day:
        return Decimal(0)

    return Decimal(str((now - day).total_seconds())) / SECONDS_PER_HOUR


def transform_costs(
    stack_id: StackId,
    source_id: SourceId,
    extracted_at: datetime,
    lines: list[CostLine],
    date_from: datetime,
    date_to: datetime,
) -> list[RowFactBilling]:
    rows_billing: list[RowFactBilling] = []
    day = date_from

    while day < date_to:
        hours = hours_in_day(day, extracted_at)

        if hours > 0:
            for line in lines:
                cost = line.cost_per_hour * hours
                quantity = line.quantity_per_hour * hours

                rows_billing.append(
                    RowFactBilling(
                        stack_id=stack_id,
                        source_id=source_id,
                        source_type=SourceType.SELFHOSTED,
                        extracted_at=extracted_at,
                        charge_period_start=day,
                        charge_period_end=day + timedelta(days=1),
                        charge_category="Usage",
                        billed_cost=cost,
                        billing_currency=CURRENCY,
                        effective_cost=cost,
                        service_name=line.service_name,
                        service_category="Compute",
                        service_provider_name="Self-hosted",
                        consumed_quantity=quantity,
                        consumed_unit=line.unit,
                        tags="{}",
                        pricing_category="Standard",
                        pricing_currency=CURRENCY,
                        pricing_quantity=quantity,
                        pricing_unit=line.unit,
                    )
                )

        day += timedelta(days=1)

    return rows_billing
