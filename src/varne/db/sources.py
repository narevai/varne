from datetime import datetime
from typing import cast

from varne.config import SourceId, StackId
from varne.db.lock import serialized
from varne.db.schema import TableName
from varne.db.types import DatabaseBackend


@serialized
def stored_source_ids(db: DatabaseBackend, stack_id: StackId) -> list[SourceId]:
    """The sources of a stack that have anything in the database."""
    found: set[SourceId] = set()

    for name in TableName:
        table = db.table(name)
        ids = table.filter(table.stack_id == stack_id).select("source_id").distinct()
        found.update(cast(list[SourceId], ids.to_pandas()["source_id"].tolist()))

    return sorted(found)


@serialized
def last_synced(db: DatabaseBackend, stack_id: StackId) -> dict[SourceId, datetime]:
    """When each source of a stack was last pulled, from what it left behind."""
    latest: dict[SourceId, datetime] = {}

    for name in TableName:
        table = db.table(name)
        df = (
            table.filter(table.stack_id == stack_id)
            .group_by("source_id")
            .aggregate(synced=table.extracted_at.max())
            .to_pandas()
        )
        for source_id, at in zip(
            cast(list[SourceId], df["source_id"].tolist()),
            cast(list[datetime], df["synced"].tolist()),
            strict=True,
        ):
            if source_id not in latest or at > latest[source_id]:
                latest[source_id] = at

    return latest


@serialized
def delete_source_data(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> None:
    """Remove everything stored for a source: what was pulled and what came of it."""
    for name in TableName:
        db.con.execute(
            f"DELETE FROM {name.value} WHERE stack_id = ? AND source_id = ?",
            [stack_id, source_id],
        )
