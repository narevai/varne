from decimal import Decimal
from typing import cast

from varne.analytics.comparison import get_container_costs
from varne.catalog.comparison import ContainerCost, image_of
from varne.config import StackId
from varne.db.lock import serialized
from varne.db.types import DatabaseBackend


@serialized
def get_container_cost_rows(
    db: DatabaseBackend, stack_id: StackId
) -> list[ContainerCost]:
    df = get_container_costs(db, stack_id).to_pandas()

    return [
        ContainerCost(
            source_id=source_id,
            name=name,
            image=image_of(tags),
            cost=Decimal(str(cost)),
            hours=Decimal(str(hours)),
        )
        for source_id, name, tags, cost, hours in zip(
            cast(list[str], df["source_id"].tolist()),
            cast(list[str], df["service_name"].tolist()),
            cast(list[str], df["tags"].tolist()),
            cast(list[object], df["cost"].tolist()),
            cast(list[object], df["hours"].tolist()),
            strict=True,
        )
    ]
