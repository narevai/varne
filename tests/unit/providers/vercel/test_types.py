import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

from varne.config import SourceType
from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.types import RowRaw
from varne.providers.vercel.transform import transform_billing
from varne.providers.vercel.types import VercelBilling


def charge(**overrides: object) -> str:
    row: dict[str, object] = {
        "ChargePeriodStart": "2026-11-01T00:00:00.000Z",
        "ChargePeriodEnd": "2026-11-02T00:00:00.000Z",
        "ChargeCategory": "Usage",
        "BilledCost": 1.5,
        "BillingCurrency": "USD",
        "EffectiveCost": 1.5,
        "ServiceName": "Edge Requests",
        "ServiceCategory": "Web",
        "ServiceProviderName": "Vercel",
        "ConsumedQuantity": 1,
        "ConsumedUnit": "Requests",
        "Tags": {},
        "PricingCategory": "Standard",
        "PricingCurrency": "USD",
        "PricingQuantity": 1,
        "PricingUnit": "Requests",
    }
    return json.dumps(row | overrides)


def test_tiny_float_costs_are_rounded_to_the_table_scale():
    billing = VercelBilling.model_validate_json(
        charge(BilledCost=6.319250895128747e-12)
    )

    assert billing.billed_cost == Decimal("0.000000000006319251")


def test_large_quantities_keep_their_integer_part():
    billing = VercelBilling.model_validate_json(
        charge(ConsumedQuantity=123456789012345.5, PricingQuantity=2.5e11)
    )

    assert billing.consumed_quantity == Decimal("123456789012345.5")
    assert billing.pricing_quantity == Decimal("250000000000")


def test_charges_that_are_not_usage_have_no_quantity_or_unit():
    billing = VercelBilling.model_validate_json(
        charge(ChargeCategory="Purchase", ConsumedQuantity=None, ConsumedUnit=None)
    )

    assert billing.consumed_quantity is None
    assert billing.consumed_unit is None


def test_charge_without_quantity_can_be_stored(db: DatabaseBackend):
    raw = RowRaw(
        stack_id="stack",
        source_id="source",
        source_type=SourceType.VERCEL,
        extracted_at=datetime(2026, 11, 18, tzinfo=UTC),
        method="GET",
        url="https://api.vercel.com/v1/billing/charges",
        payload=charge(ConsumedQuantity=None, ConsumedUnit=None),
    )

    rows = transform_billing(raw)
    db.insert(TableName.FACT_BILLING, [row.model_dump() for row in rows])

    assert cast(int, db.table(TableName.FACT_BILLING).count().execute()) == 1
