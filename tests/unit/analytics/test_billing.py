from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

from tests.unit.providers.test_replace import FakeService, billing, day

from varne.analytics.billing import get_billing_per_day
from varne.db.types import DatabaseBackend

AT = datetime(2026, 9, 10, 8, 0, tzinfo=UTC)


def fill(db: DatabaseBackend) -> None:
    a = FakeService(db, "stack", "a")
    a.replace_fact_billing(
        [billing("a", 1, AT, "2"), billing("a", 1, AT, "3")], day(1), day(2)
    )
    b = FakeService(db, "other_stack", "b")
    row = billing("b", 1, AT, "100").model_copy(update={"stack_id": "other_stack"})
    b.replace_fact_billing([row], day(1), day(2))


def test_cost_per_day_can_be_limited_to_one_stack(db: DatabaseBackend):
    fill(db)

    df = get_billing_per_day(db, "stack").to_pandas()

    assert cast(list[str], df["stack_id"].tolist()) == ["stack"]
    assert df["cost"].iloc[0] == Decimal("5")


def test_cost_per_day_without_a_stack_still_covers_everything(db: DatabaseBackend):
    fill(db)

    df = get_billing_per_day(db).to_pandas()

    assert sorted(cast(list[str], df["stack_id"].tolist())) == ["other_stack", "stack"]
