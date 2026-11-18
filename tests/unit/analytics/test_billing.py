from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

from varne.analytics.billing import get_billing_per_day
from varne.config import SourceType
from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.types import RowFactBilling

DAY = datetime(2026, 9, 1, tzinfo=UTC)


def billing(stack_id: str, source_id: str, cost: str) -> RowFactBilling:
    return RowFactBilling(
        stack_id=stack_id,
        source_id=source_id,
        source_type=SourceType.VERCEL,
        extracted_at=datetime(2026, 9, 10, 8, 0, tzinfo=UTC),
        charge_period_start=DAY,
        charge_period_end=datetime(2026, 9, 2, tzinfo=UTC),
        charge_category="Usage",
        billed_cost=Decimal(cost),
        billing_currency="USD",
        effective_cost=Decimal(cost),
        service_name="svc",
        service_category="cat",
        service_provider_name="Vercel",
        consumed_quantity=Decimal(1),
        consumed_unit="x",
        tags="{}",
        pricing_category="p",
        pricing_currency="USD",
        pricing_quantity=Decimal(1),
        pricing_unit="x",
    )


def fill(db: DatabaseBackend) -> None:
    rows = [billing("stack", "a", "5"), billing("other_stack", "b", "100")]
    db.insert(TableName.FACT_BILLING, [row.model_dump() for row in rows])


def test_cost_per_day_can_be_limited_to_one_stack(db: DatabaseBackend):
    fill(db)

    df = get_billing_per_day(db, "stack").to_pandas()

    assert cast(list[str], df["stack_id"].tolist()) == ["stack"]
    assert df["cost"].iloc[0] == Decimal("5")


def test_cost_per_day_without_a_stack_still_covers_everything(db: DatabaseBackend):
    fill(db)

    df = get_billing_per_day(db).to_pandas()

    assert sorted(cast(list[str], df["stack_id"].tolist())) == ["other_stack", "stack"]
