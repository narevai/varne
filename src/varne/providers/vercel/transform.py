from datetime import datetime

from pydantic import TypeAdapter

from varne.providers.types import RowDimSourceMeta, RowFactBilling, RowFactUsage, RowRaw
from varne.providers.vercel.types import (
    VercelBilling,
    VercelProjectsResponse,
    VercelWebAnalyticsAggregateItem,
)


def project_to_meta(row_raw: RowRaw, value_name: str, value: str) -> RowDimSourceMeta:
    row_staging: RowDimSourceMeta = RowDimSourceMeta(
        stack_id=row_raw.stack_id,
        source_id=row_raw.source_id,
        source_type=row_raw.source_type,
        extracted_at=row_raw.extracted_at,
        value_name=value_name,
        value=value,
    )

    return row_staging


def transform_meta(row: RowRaw) -> list[RowDimSourceMeta]:
    rows_staging: list[RowDimSourceMeta] = []
    adapter = TypeAdapter(VercelProjectsResponse)
    projects_typed = adapter.validate_json(row.payload)

    for project in projects_typed.projects:
        row_id: RowDimSourceMeta = project_to_meta(
            row, value_name="id", value=project.id
        )
        row_name: RowDimSourceMeta = project_to_meta(
            row, value_name="name", value=project.name
        )
        row_account_id: RowDimSourceMeta = project_to_meta(
            row, value_name="account_id", value=project.account_id
        )
        rows_staging.append(row_id)
        rows_staging.append(row_name)
        rows_staging.append(row_account_id)

    return rows_staging


def transform_billing(row: RowRaw) -> list[RowFactBilling]:
    rows_billing: list[RowFactBilling] = []
    response_typed = [
        VercelBilling.model_validate_json(line)
        for line in row.payload.splitlines()
        if line.strip()
    ]

    for b in response_typed:
        row_billing = RowFactBilling(
            stack_id=row.stack_id,
            source_id=row.source_id,
            source_type=row.source_type,
            extracted_at=row.extracted_at,
            charge_period_start=b.charge_period_start,
            charge_period_end=b.charge_period_end,
            charge_category=b.charge_category,
            billed_cost=b.billed_cost,
            billing_currency=b.billing_currency,
            effective_cost=b.effective_cost,
            service_name=b.service_name,
            service_category=b.service_category,
            service_provider_name=b.service_provider_name,
            consumed_quantity=b.consumed_quantity,
            consumed_unit=b.consumed_unit,
            tags=str(b.tags),
            pricing_category=b.pricing_category,
            pricing_currency=b.pricing_currency,
            pricing_quantity=b.pricing_quantity,
            pricing_unit=b.pricing_unit,
        )
        rows_billing.append(row_billing)

    return rows_billing


def web_analytics_to_usage(
    row_raw: RowRaw, event_time: datetime, usage_name: str, usage: int
) -> RowFactUsage:
    row = RowFactUsage(
        stack_id=row_raw.stack_id,
        source_id=row_raw.source_id,
        source_type=row_raw.source_type,
        extracted_at=row_raw.extracted_at,
        event_time=event_time,
        usage_name=usage_name,
        usage=usage,
    )

    return row


def transform_analytics_aggregate(row: RowRaw) -> list[RowFactUsage]:
    rows_usage: list[RowFactUsage] = []
    response_typed = [
        VercelWebAnalyticsAggregateItem.model_validate_json(line)
        for line in row.payload.splitlines()
        if line.strip()
    ]

    for r in response_typed:
        for u in r.data:
            row_visitors: RowFactUsage = web_analytics_to_usage(
                row, event_time=u.timestamp, usage_name="visitors", usage=u.visitors
            )
            row_pageviews: RowFactUsage = web_analytics_to_usage(
                row, event_time=u.timestamp, usage_name="visitors", usage=u.pageviews
            )
            rows_usage.append(row_visitors)
            rows_usage.append(row_pageviews)

    return rows_usage
