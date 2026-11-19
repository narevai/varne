import json
from datetime import UTC, datetime
from decimal import Decimal

from varne.config import SourceType
from varne.providers.openai.transform import transform_costs
from varne.providers.types import RowRaw


def raw(results: list[dict[str, object]]) -> RowRaw:
    payload = {
        "object": "page",
        "data": [
            {
                "object": "bucket",
                "start_time": 1730419200,
                "end_time": 1730505600,
                "results": results,
            }
        ],
        "has_more": False,
        "next_page": None,
    }
    return RowRaw(
        stack_id="stack",
        source_id="source",
        source_type=SourceType.OPENAI,
        extracted_at=datetime(2026, 11, 18, tzinfo=UTC),
        method="GET",
        url="https://api.openai.com/v1/organization/costs",
        payload=json.dumps(payload),
    )


def test_cost_becomes_a_billing_row_in_dollars():
    rows = transform_costs(
        raw(
            [
                {
                    "amount": {"value": 0.06, "currency": "usd"},
                    "line_item": "gpt-5, input",
                    "project_id": "proj_1",
                    "quantity": 1500,
                    "quantity_unit": "tokens",
                }
            ]
        )
    )

    assert len(rows) == 1
    assert rows[0].billed_cost == Decimal("0.06")
    assert rows[0].effective_cost == rows[0].billed_cost
    assert rows[0].billing_currency == "USD"
    assert rows[0].service_name == "gpt-5, input"
    assert rows[0].service_provider_name == "OpenAI"
    assert rows[0].consumed_quantity == Decimal(1500)
    assert rows[0].consumed_unit == "tokens"
    assert json.loads(rows[0].tags) == {"project_id": "proj_1"}
    assert rows[0].charge_period_start == datetime(2024, 11, 1, tzinfo=UTC)


def test_result_without_amount_is_skipped():
    assert transform_costs(raw([{"line_item": "x"}])) == []


def test_ungrouped_result_gets_a_default_service_name():
    rows = transform_costs(raw([{"amount": {"value": 1, "currency": "usd"}}]))

    assert rows[0].service_name == "OpenAI API"
    assert rows[0].consumed_quantity is None
