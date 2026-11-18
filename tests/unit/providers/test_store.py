from datetime import UTC, datetime
from decimal import Decimal
from typing import cast, override

from varne.config import SourceType
from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.base import ProviderService
from varne.providers.types import RowFactBilling

AT = datetime(2026, 11, 18, 8, 30, tzinfo=UTC)


class FakeService(ProviderService):
    @property
    @override
    def provider(self) -> str:
        return "fake"

    @override
    def fetch_source_meta(self) -> None:
        pass

    @override
    def fetch_source_data(self) -> None:
        pass


def charge(quantity: Decimal | None, unit: str | None) -> RowFactBilling:
    return RowFactBilling(
        stack_id="stack",
        source_id="source",
        source_type=SourceType.VERCEL,
        extracted_at=AT,
        charge_period_start=datetime(2026, 11, 1, tzinfo=UTC),
        charge_period_end=datetime(2026, 11, 2, tzinfo=UTC),
        charge_category="Usage",
        billed_cost=Decimal("1.5"),
        billing_currency="USD",
        effective_cost=Decimal("1.5"),
        service_name="svc",
        service_category="cat",
        service_provider_name="Vercel",
        consumed_quantity=quantity,
        consumed_unit=unit,
        tags="{}",
        pricing_category="p",
        pricing_currency="USD",
        pricing_quantity=Decimal(1),
        pricing_unit="x",
    )


def test_charges_with_and_without_quantity_can_be_stored_together(
    db: DatabaseBackend,
):
    service = FakeService(db, "stack", "source")

    service.store_fact_billing([charge(Decimal("2"), "GB"), charge(None, None)])

    table = db.table(TableName.FACT_BILLING)
    assert cast(int, table.count().execute()) == 2
    without_quantity = table.filter(table.consumed_quantity.isnull())
    assert cast(int, without_quantity.count().execute()) == 1


def test_stored_timestamps_keep_their_utc_time(db: DatabaseBackend):
    FakeService(db, "stack", "source").store_fact_billing([charge(None, None)])

    stored = db.table(TableName.FACT_BILLING).extracted_at.max().execute()

    assert stored == AT.replace(tzinfo=None)
