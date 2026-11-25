from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest

from varne.analytics.comparison import get_container_cost_rows
from varne.catalog.comparison import compare
from varne.catalog.images import identify
from varne.db.sources import last_synced, stored_source_ids
from varne.db.types import DatabaseBackend
from varne.demo import DEMO_STACK_ID
from varne.demo.seed import reset_demo, seed_demo
from varne.demo.usage import CONTAINERS, SYSTEM, DemoUsage
from varne.dependencies import get_config_manager, get_db, get_http
from varne.providers.docker.rates import cost_lines
from varne.providers.docker.service import DockerService
from varne.providers.docker.usage import SYSTEM_ENTITY
from varne.settings import Settings, get_settings

NOW = datetime(2026, 11, 20, 15, tzinfo=UTC)  # a Friday


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

    seed_demo()
    synced = last_synced(get_db(), DEMO_STACK_ID)
    seed_demo()

    assert stored_source_ids(get_db(), DEMO_STACK_ID) == ["homelab"]
    # the second run found the data and left it alone
    assert last_synced(get_db(), DEMO_STACK_ID) == synced
    # and the data is about the last days, up to now
    assert synced["homelab"].replace(tzinfo=UTC) <= datetime.now(UTC) + timedelta(
        minutes=1
    )


def test_the_demo_does_not_touch_the_database_of_the_real_app(demo: Path):
    reset_demo(Path(get_settings().config_path), Path(get_settings().database_path))

    get_db()

    assert (demo / "demo.duckdb").exists()
    assert not (demo / "app.duckdb").exists()


def fetched(day_count: int = 10):
    return DemoUsage(lambda: NOW).fetch(NOW - timedelta(days=day_count), lambda _: None)


def test_the_made_up_host_has_every_hour_of_the_days_it_looks_at():
    usage = fetched(2)

    hours = {item.hour for item in usage.hours}
    assert min(hours) == (NOW - timedelta(days=2)).replace(minute=0)
    assert max(hours) == NOW.replace(minute=0)
    # both ends are hours of data: the first one that is asked for and this one
    assert len(hours) == 2 * 24 + 1
    assert {item.entity for item in usage.hours} == {
        SYSTEM_ENTITY,
        *(c.name for c in CONTAINERS),
    }


def test_the_made_up_host_is_the_same_every_time():
    assert fetched() == fetched()


def test_the_containers_are_applications_the_catalog_knows():
    apps = [identify(c.image) for c in CONTAINERS]

    assert all(apps)
    assert sum(1 for app in apps if app and app.alternative) == 12


def test_a_container_is_not_as_busy_every_day():
    usage = fetched()

    per_day: dict[str, int] = {}
    for item in usage.hours:
        if item.entity == CONTAINERS[0].name and item.metric == "cpu":
            per_day[item.hour.date().isoformat()] = (
                per_day.get(item.hour.date().isoformat(), 0) + item.value
            )

    full_days = [total for day, total in per_day.items() if day != "2026-11-20"]
    assert max(full_days) > 1.3 * min(full_days)


def test_the_weekend_is_not_a_weekday():
    usage = fetched()

    def busyness(names: set[str], weekend: bool) -> float:
        values = [
            item.value
            for item in usage.hours
            if item.entity in names
            and item.metric == "cpu"
            and (item.hour.weekday() >= 5) == weekend
        ]
        return sum(values) / len(values)

    work = {c.name for c in CONTAINERS if c.weekend < 1}
    play = {c.name for c in CONTAINERS if c.weekend > 1.3}
    assert busyness(work, True) < busyness(work, False)
    assert busyness(play, True) > busyness(play, False)


def test_the_made_up_host_shows_a_homelab_that_pays_for_itself(db: DatabaseBackend):
    DockerService(
        db,
        DemoUsage(lambda: NOW),
        "demo",
        "homelab",
        cost_lines(
            hourly_cost=None,
            machine_cost=Decimal(1200),
            amortization_years=Decimal(6),
            power_draw_watts=Decimal(40),
            electricity_price_per_kwh=Decimal("0.2"),
        ),
        lookback_days=10,
        now=lambda: NOW,
    ).fetch_source_data()

    comparison = compare(get_container_cost_rows(db, "demo"))

    compared = [app for app in comparison.apps if app.alternative]
    assert len(comparison.apps) == 13
    assert len(compared) == 12
    # about a third of the machine is idle, most of it is used
    assert 0.2 < comparison.idle / comparison.machine_cost < 0.5
    assert comparison.roi is not None and comparison.roi > 1
    assert SYSTEM not in {app.app for app in comparison.apps}
