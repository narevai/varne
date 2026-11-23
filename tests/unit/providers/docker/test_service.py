from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import ibis

from varne.db.schema import TableName
from varne.db.types import DatabaseBackend
from varne.providers.beszel.usage import BeszelUsage
from varne.providers.docker.rates import CostLine
from varne.providers.docker.service import DockerService

# The recorded hub has the last hour of the 20th of November 2026 in it.
NOW = datetime(2026, 11, 20, 15, tzinfo=UTC)
LINES = [
    CostLine("Hardware amortization", Decimal(1), Decimal(1), "hours"),
    CostLine("Electricity", Decimal("0.1"), Decimal("0.2"), "kWh"),
]


def service(db: DatabaseBackend, usage: BeszelUsage) -> DockerService:
    return DockerService(
        db, usage, "stack", "source", LINES, lookback_days=1, now=lambda: NOW
    )


def test_pull_books_the_cost_of_the_whole_machine(
    db: DatabaseBackend, beszel_usage: BeszelUsage
):
    service(db, beszel_usage).fetch_source_data()

    billing = db.table(TableName.FACT_BILLING)
    totals = billing.group_by("source_id").aggregate(total=ibis._.billed_cost.sum())
    total = cast(list[object], totals.execute()["total"].tolist())[0]
    # the machine cost 1.1 for each of the 39 hours from the 19th until 15:00
    assert Decimal(str(total)) == Decimal("1.1") * 39
    assert set(cast(list[str], billing.source_type.execute().tolist())) == {"docker"}


def test_the_cost_is_split_over_the_containers_and_idle_capacity(
    db: DatabaseBackend, beszel_usage: BeszelUsage
):
    service(db, beszel_usage).fetch_source_data()

    services = set(
        cast(
            list[str], db.table(TableName.FACT_BILLING).service_name.execute().tolist()
        )
    )
    assert "Idle" in services
    assert "compose-lab-elastic-search-1" in services
    assert len(services) > 100


def test_the_image_of_a_container_is_kept_with_its_cost(
    db: DatabaseBackend, beszel_usage: BeszelUsage
):
    service(db, beszel_usage).fetch_source_data()

    billing = db.table(TableName.FACT_BILLING)
    tags = billing.filter(billing.service_name == "compose-lab-elastic-search-1").tags
    assert set(cast(list[str], tags.execute().tolist())) == {
        '{"system": "compose-lab", "image": "docker.elastic.co/elasticsearch/elasticsearch:9.5.4"}'
    }


def test_usage_is_stored_with_the_capacity_of_the_machine(
    db: DatabaseBackend, beszel_usage: BeszelUsage
):
    service(db, beszel_usage).fetch_source_data()

    names = set(
        cast(list[str], db.table(TableName.FACT_USAGE).usage_name.execute().tolist())
    )
    assert {
        "compose-lab/system/cpu",
        "compose-lab/system/memory_total",
        "compose-lab/compose-lab-elastic-search-1/memory",
    } <= names


def test_everything_pulled_shares_one_extracted_at(
    db: DatabaseBackend, beszel_usage: BeszelUsage
):
    service(db, beszel_usage).fetch_source_data()

    for name in (TableName.FACT_USAGE, TableName.FACT_BILLING, TableName.RAW):
        stamps = db.table(name).extracted_at.nunique().execute()
        assert cast(int, stamps) == 1


def test_the_responses_of_the_hub_are_kept_raw(
    db: DatabaseBackend, beszel_usage: BeszelUsage
):
    service(db, beszel_usage).fetch_source_data()

    assert cast(int, db.table(TableName.RAW).count().execute()) > 10


def test_sync_stores_the_systems_and_the_rates(
    db: DatabaseBackend, beszel_usage: BeszelUsage
):
    service(db, beszel_usage).fetch_source_meta()

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
        ("system", "compose-lab"),
    ]
