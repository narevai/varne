import json
from decimal import Decimal

from varne.providers.anthropic.types import AnthropicCostReport
from varne.providers.types import RowFactBilling, RowRaw

CENTS_PER_UNIT = Decimal(100)


def transform_cost_report(row: RowRaw) -> list[RowFactBilling]:
    rows_billing: list[RowFactBilling] = []
    report = AnthropicCostReport.model_validate_json(row.payload)

    for bucket in report.data:
        for result in bucket.results:
            cost = result.amount / CENTS_PER_UNIT
            tags = {
                key: value
                for key, value in {
                    "workspace_id": result.workspace_id,
                    "model": result.model,
                    "cost_type": result.cost_type,
                    "token_type": result.token_type,
                    "service_tier": result.service_tier,
                    "context_window": result.context_window,
                }.items()
                if value is not None
            }

            rows_billing.append(
                RowFactBilling(
                    stack_id=row.stack_id,
                    source_id=row.source_id,
                    source_type=row.source_type,
                    extracted_at=row.extracted_at,
                    charge_period_start=bucket.starting_at,
                    charge_period_end=bucket.ending_at,
                    charge_category="Usage",
                    billed_cost=cost,
                    billing_currency=result.currency,
                    effective_cost=cost,
                    service_name=result.description or "Claude API",
                    service_category="AI and Machine Learning",
                    service_provider_name="Anthropic",
                    consumed_quantity=None,
                    consumed_unit=None,
                    tags=json.dumps(tags, sort_keys=True),
                    pricing_category=(result.service_tier or "standard").title(),
                    pricing_currency=result.currency,
                    pricing_quantity=Decimal(0),
                    pricing_unit="",
                )
            )

    return rows_billing
