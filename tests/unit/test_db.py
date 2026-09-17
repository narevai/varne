from varne.db.schema import TableName
from varne.db.types import DatabaseBackend


def test_ibis_connection(db: DatabaseBackend):
    result = db.sql("SELECT 1 AS value").execute()
    assert result["value"].iloc[0] == 1  # pyright: ignore[reportAttributeAccessIssue]


def test_db_table_create(db: DatabaseBackend):
    tables_db = db.list_tables().sort()
    tables_expected = [TableName.RAW.value, TableName.DIM_SOURCE_META.value].sort()
    assert tables_db == tables_expected
