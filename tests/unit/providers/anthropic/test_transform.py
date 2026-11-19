import json
from datetime import UTC, datetime
from decimal import Decimal

from varne.config import SourceType
from varne.providers.anthropic.transform import transform_cost_report
from varne.providers.types import RowRaw


def result(amount: str, **fields: str | None) -> dict[str, str | None]:
    return {
        "amount": amount,
        "currency": "USD",
        "description": "Claude Opus 5.5 Usage - Input Tokens",
        "cost_type": "tokens",
        "model": "claude-opus-5-5",
        "token_type": "uncached_input_tokens",
        "service_tier": "standard",
        "context_window": "0-200k",
        "workspace_id": "wrkspc_1",
        **fields,
    }


def page(next_page: str | None, amounts: list[str]) -> dict[str, object]:
    return {
        "data": [
            {
                "starting_at": "2026-09-01T00:00:00Z",
                "ending_at": "2026-09-02T00:00:00Z",
                "results": [result(amount) for amount in amounts],
            },
            {
                "starting_at": "2026-09-02T00:00:00Z",
                "ending_at": "2026-09-03T00:00:00Z",
                "results": [],
            },
        ],
        "has_more": next_page is not None,
        "next_page": next_page,
    }


def raw(payload: dict[str, object]) -> RowRaw:
    return RowRaw(
        stack_id="stack",
        source_id="source",
        source_type=SourceType.ANTHROPIC,
        extracted_at=datetime(2026, 9, 10, tzinfo=UTC),
        method="GET",
        url="https://api.anthropic.com/v1/organizations/cost_report",
        payload=json.dumps(payload),
    )


def test_amount_in_cents_becomes_dollars():
    rows = transform_cost_report(raw(page(None, ["123.78912"])))

    assert len(rows) == 1
    assert rows[0].billed_cost == Decimal("1.2378912")
    assert rows[0].effective_cost == rows[0].billed_cost
    assert rows[0].billing_currency == "USD"
    assert rows[0].service_provider_name == "Anthropic"
    assert rows[0].consumed_quantity is None
    assert json.loads(rows[0].tags)["model"] == "claude-opus-5-5"


def test_empty_buckets_give_no_rows():
    assert transform_cost_report(raw({"data": [], "has_more": False})) == []
