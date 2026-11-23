from collections.abc import Generator
from pathlib import Path

import httpx2 as httpx
import pytest
from fastapi.testclient import TestClient
from tests.beszel import recorded_hub

from varne.db.connection import create_connection
from varne.db.schema import create_tables
from varne.http import create_http_client
from varne.providers.beszel.usage import BeszelUsage


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
    client.headers["Accept-Encoding"] = "identity"
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


@pytest.fixture
def beszel_usage(http_client: httpx.Client) -> Generator[BeszelUsage]:
    with recorded_hub(http_client) as usage:
        yield usage
