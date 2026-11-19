from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.selfhosted.rates import CostLine
from varne.providers.selfhosted.service import SelfHostedService

LINES = [
    CostLine("Hardware amortization", Decimal(1), Decimal(1), "hours"),
    CostLine("Electricity", Decimal("0.1"), Decimal("0.2"), "kWh"),
]


def service(db: DatabaseBackend, now: datetime) -> SelfHostedService:
    return SelfHostedService(
        db,
        "stack",
        "source",
        LINES,
        lookback_days=2,
        now=lambda: now,
    )


def test_pull_writes_a_row_per_line_for_every_day_including_today(db: DatabaseBackend):
    service(db, datetime(2026, 9, 10, 12, tzinfo=UTC)).fetch_source_data()

    # 2 days back + today, 2 lines each
    assert cast(int, db.table(TableName.FACT_BILLING).count().execute()) == 6
    assert cast(int, db.table(TableName.RAW).count().execute()) == 0


def test_all_rows_of_a_pull_share_one_extracted_at(db: DatabaseBackend):
    service(db, datetime(2026, 9, 10, 12, tzinfo=UTC)).fetch_source_data()

    stamps = db.table(TableName.FACT_BILLING).extracted_at.nunique().execute()
    assert cast(int, stamps) == 1


def test_sync_stores_the_rates_as_metadata(db: DatabaseBackend):
    service(db, datetime(2026, 9, 10, 12, tzinfo=UTC)).fetch_source_meta()

    table = db.table(TableName.DIM_SOURCE_META)
    pairs = sorted(
        zip(
            cast(list[str], table.value_name.execute().tolist()),
            cast(list[str], table.value.execute().tolist()),
            strict=True,
        )
    )
    assert pairs == [
        ("Electricity per hour", "0.100000 USD"),
        ("Hardware amortization per hour", "1.000000 USD"),
    ]
