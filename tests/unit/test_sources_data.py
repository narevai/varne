from datetime import UTC, datetime

from varne.config import SourceType
from varne.db.schema import TableName
from varne.db.sources import delete_source_data, last_synced, stored_source_ids
from varne.db.types import DatabaseBackend
from varne.providers.types import RowDimSourceMeta, RowFactUsage

AT = datetime(2026, 11, 18, 12, tzinfo=UTC)


def fill(db: DatabaseBackend) -> None:
    meta = [
        RowDimSourceMeta(
            stack_id=stack,
            source_id=source,
            source_type=SourceType.ANTHROPIC,
            extracted_at=AT,
            value_name="n",
            value="v",
        )
        for stack, source in [("s", "a"), ("s", "b"), ("other", "a")]
    ]
    db.insert(TableName.DIM_SOURCE_META, [row.model_dump() for row in meta])
    usage = RowFactUsage(
        stack_id="s",
        source_id="c",
        source_type=SourceType.ANTHROPIC,
        extracted_at=AT,
        event_time=AT,
        usage_name="u",
        usage=1,
    )
    db.insert(TableName.FACT_USAGE, [usage.model_dump()])


def test_sources_with_anything_stored_are_listed_per_stack(db: DatabaseBackend):
    fill(db)

    assert stored_source_ids(db, "s") == ["a", "b", "c"]
    assert stored_source_ids(db, "other") == ["a"]
    assert stored_source_ids(db, "nothing") == []


def test_deleting_a_source_leaves_the_others_alone(db: DatabaseBackend):
    fill(db)

    delete_source_data(db, "s", "a")
    delete_source_data(db, "s", "c")

    assert stored_source_ids(db, "s") == ["b"]
    assert stored_source_ids(db, "other") == ["a"]


def test_a_source_was_last_synced_when_it_left_something_behind_last(
    db: DatabaseBackend,
):
    fill(db)
    later = datetime(2026, 11, 20, 8, tzinfo=UTC)
    usage = RowFactUsage(
        stack_id="s",
        source_id="a",
        source_type=SourceType.ANTHROPIC,
        extracted_at=later,
        event_time=later,
        usage_name="u",
        usage=1,
    )
    db.insert(TableName.FACT_USAGE, [usage.model_dump()])

    synced = last_synced(db, "s")

    assert {k: v.replace(tzinfo=UTC) for k, v in synced.items()} == {
        "a": later,
        "b": AT,
        "c": AT,
    }
    assert last_synced(db, "nothing") == {}
