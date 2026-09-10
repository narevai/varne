from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from varne.db.connection import create_connection
from varne.db.schema import create_tables
from varne.http import create_http_client


@pytest.fixture
def vcr_config():
    return {
        "decode_compressed_response": True,
        "filter_headers": ["authorization"],
    }


@pytest.fixture
def client() -> TestClient:
    from varne.app import app

    return TestClient(app)


@pytest.fixture
def db(tmp_path: Path):
    path_db = tmp_path / "test.duckdb"
    connection = create_connection(path_db)

    create_tables(connection)
    yield connection


@pytest.fixture
def http_client():
    client = create_http_client()

    yield client

    client.close()


@pytest.fixture
def config_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "config" / "varne.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        """
stacks:
  - id: stack_test
    name: Test Stack
    sources:
      - id: source_test
        name: Test Source
"""
    )

    return path
