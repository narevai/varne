import json
from decimal import Decimal

from varne.providers.openai.types import OpenAICostsPage
from varne.providers.types import RowFactBilling, RowRaw


def transform_costs(row: RowRaw) -> list[RowFactBilling]:
    rows_billing: list[RowFactBilling] = []
    page = OpenAICostsPage.model_validate_json(row.payload)

    for bucket in page.data:
        for result in bucket.results:
            if result.amount is None:
                continue

            currency = result.amount.currency.upper()
            tags = (
                {} if result.project_id is None else {"project_id": result.project_id}
            )

            rows_billing.append(
                RowFactBilling(
                    stack_id=row.stack_id,
                    source_id=row.source_id,
                    source_type=row.source_type,
                    extracted_at=row.extracted_at,
                    charge_period_start=bucket.start_time,
                    charge_period_end=bucket.end_time,
                    charge_category="Usage",
                    billed_cost=result.amount.value,
                    billing_currency=currency,
                    effective_cost=result.amount.value,
                    service_name=result.line_item or "OpenAI API",
                    service_category="AI and Machine Learning",
                    service_provider_name="OpenAI",
                    consumed_quantity=result.quantity,
                    consumed_unit=result.quantity_unit,
                    tags=json.dumps(tags, sort_keys=True),
                    pricing_category="Standard",
                    pricing_currency=currency,
                    pricing_quantity=Decimal(0),
                    pricing_unit="",
                )
            )

    return rows_billing
