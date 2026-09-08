from varne.db.types import DatabaseBackend


def test_ibis_connection(db: DatabaseBackend):
    result = db.sql("SELECT 1 AS value").execute()
    assert result["value"].iloc[0] == 1  # pyright: ignore[reportAttributeAccessIssue]


def test_db_table_create(db: DatabaseBackend):
    assert db.list_tables() == ["raw", "staging"]
