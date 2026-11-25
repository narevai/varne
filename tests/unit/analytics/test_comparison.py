from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

from varne.analytics.comparison import get_container_costs
from varne.catalog.comparison import ContainerCost, compare, image_of
from varne.db.types import DatabaseBackend
from varne.providers.beszel.usage import BeszelUsage
from varne.providers.docker.rates import CostLine
from varne.providers.docker.service import DockerService

# The recorded hub has the last hour of the 20th of November 2026 in it.
NOW = datetime(2026, 11, 20, 15, tzinfo=UTC)


def test_costs_come_from_the_billing_of_docker_sources(
    db: DatabaseBackend, beszel_usage: BeszelUsage
):
    DockerService(
        db,
        beszel_usage,
        "stack",
        "source",
        [CostLine("Hosting", Decimal(1), Decimal(1), "hours")],
        lookback_days=1,
        now=lambda: NOW,
    ).fetch_source_data()

    df = get_container_costs(db, "stack").to_pandas()

    names = cast(list[str], df["service_name"].tolist())
    assert "Idle" in names and "compose-lab-elastic-search-1" in names
    assert sum(cast(list[Decimal], df["cost"].tolist()), Decimal(0)) == Decimal(2)
    assert len(get_container_costs(db, "another stack").to_pandas()) == 0

    costs = [
        ContainerCost(
            source_id,
            name,
            image_of(tags),
            Decimal(str(amount)),
            Decimal(str(hours)),
        )
        for source_id, name, tags, amount, hours in zip(
            cast(list[str], df["source_id"].tolist()),
            names,
            cast(list[str], df["tags"].tolist()),
            cast(list[object], df["cost"].tolist()),
            cast(list[object], df["hours"].tolist()),
            strict=True,
        )
    ]
    comparison = compare(costs)

    # a machine that costs 1 an hour costs 730 in a month, however long it was watched
    assert round(comparison.machine_cost, 2) == Decimal(730)
    assert comparison.idle < comparison.machine_cost
    assert comparison.apps[0].app == "Elasticsearch"
    assert comparison.apps[0].containers == ("compose-lab-elastic-search-1",)
