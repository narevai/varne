from datetime import UTC
from pathlib import Path
from typing import cast

import pytest

from varne.cassettes import CassetteManager
from varne.db.sources import last_synced, stored_source_ids
from varne.demo import DEMO_CASSETTE, DEMO_NOW, DEMO_STACK_ID
from varne.demo.seed import reset_demo, seed_demo
from varne.dependencies import get_config_manager, get_db, get_http
from varne.settings import Settings, get_settings


@pytest.fixture
def demo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The app set up as a demo, on files of its own."""
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "app.duckdb"))
    monkeypatch.setenv("CONFIG_PATH", str(tmp_path / "varne.yaml"))
    caches = (get_config_manager, get_db, get_http, get_settings)
    for cached in caches:
        cached.cache_clear()
    yield tmp_path
    for cached in caches:
        cached.cache_clear()


def test_the_demo_is_off_unless_it_is_asked_for():
    assert cast(bool, Settings.model_fields["demo_mode"].default) is False


def test_the_demo_has_a_database_and_a_configuration_of_its_own(tmp_path: Path):
    settings = Settings(
        demo_mode=True,
        database_path=str(tmp_path / "app.duckdb"),
        config_path=str(tmp_path / "varne.yaml"),
    )

    assert settings.database_path == str(tmp_path / "demo.duckdb")
    assert settings.config_path == str(tmp_path / "demo.yaml")


def test_without_the_demo_the_files_are_yours(tmp_path: Path):
    settings = Settings(
        demo_mode=False,
        database_path=str(tmp_path / "app.duckdb"),
        config_path=str(tmp_path / "varne.yaml"),
    )

    assert settings.database_path == str(tmp_path / "app.duckdb")
    assert settings.config_path == str(tmp_path / "varne.yaml")


def test_a_restart_puts_the_demo_back_as_it_was(tmp_path: Path):
    config = tmp_path / "demo.yaml"
    database = tmp_path / "demo.duckdb"
    config.write_text("stacks: []\n")
    database.write_text("changed")
    database.with_name("demo.duckdb.wal").write_text("changed")

    reset_demo(config, database)

    assert "type: docker" in config.read_text()
    assert not database.exists()
    assert not database.with_name("demo.duckdb.wal").exists()


@pytest.mark.usefixtures("demo")
def test_the_demo_fills_itself_in_once():
    reset_demo(Path(get_settings().config_path), Path(get_settings().database_path))
    manager = CassetteManager([DEMO_CASSETTE])
    manager.start()
    try:
        seed_demo()
        synced = last_synced(get_db(), DEMO_STACK_ID)
        seed_demo()
    finally:
        manager.stop()

    assert stored_source_ids(get_db(), DEMO_STACK_ID) == ["homelab"]
    # the second run found the data and left it alone
    assert last_synced(get_db(), DEMO_STACK_ID) == synced
    # and the data is about the days of the recording, not about today
    assert synced["homelab"].replace(tzinfo=UTC) <= DEMO_NOW


def test_the_demo_does_not_touch_the_database_of_the_real_app(demo: Path):
    reset_demo(Path(get_settings().config_path), Path(get_settings().database_path))

    get_db()

    assert (demo / "demo.duckdb").exists()
    assert not (demo / "app.duckdb").exists()
