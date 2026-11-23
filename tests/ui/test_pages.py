from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from nicegui import ui
from nicegui.testing import User
from tests.beszel import recorded_hub

from varne.config import SourceType
from varne.db.schema import TableName
from varne.dependencies import get_db, get_http
from varne.providers.docker.rates import CostLine
from varne.providers.docker.service import DockerService
from varne.providers.types import RowFactUsage


@pytest.mark.usefixtures("config_path")
async def test_page_dashboard(user: User) -> None:
    await user.open("/")
    await user.should_see("Dashboard")


@pytest.mark.usefixtures("config_path")
async def test_page_settings(user: User) -> None:
    await user.open("/settings")
    await user.should_see("Settings")
    await user.should_see("stack_test")


@pytest.mark.usefixtures("config_path")
async def test_sidebar_links_to_the_documentation(user: User) -> None:
    await user.open("/")

    await user.should_see("Documentation")
    link = user.find("Documentation").elements.pop()
    item = next(parent for parent in link.ancestors() if parent.props.get("href"))
    assert item.props["href"] == "https://www.narev.ai/docs/varne"
    assert item.props["target"] == "_blank"


TWO_SOURCES = """
stacks:
  - id: stack_a
    name: Stack A
    sources:
      - id: first
        name: First Source
        type: jsonplaceholder
      - id: second
        name: Second Source
        type: jsonplaceholder
  - id: stack_b
    name: Stack B
    sources:
      - id: third
        name: Third Source
        type: jsonplaceholder
"""


async def test_dashboard_shows_a_card_for_every_source_of_the_stack(
    user: User, config_path: Path
) -> None:
    config_path.write_text(TWO_SOURCES)

    await user.open("/")

    await user.should_see("First Source")
    await user.should_see("Second Source")
    await user.should_not_see("Third Source")  # another stack


async def test_reload_config_with_no_stacks_does_not_crash(
    user: User, config_path: Path
) -> None:
    config_path.write_text("stacks: []\n")
    await user.open("/")

    user.find(kind=ui.button, content="reload config").click()

    await user.should_see("Configuration loaded")


async def test_reload_config_reports_a_broken_file(
    user: User, config_path: Path
) -> None:
    config_path.write_text("stacks: []\n")
    await user.open("/")
    config_path.write_text("stacks:\n  - id: only_an_id\n")

    user.find(kind=ui.button, content="reload config").click()

    await user.should_see("Configuration failed to load")
    await user.should_not_see("Configuration loaded")


async def test_reload_config_picks_up_new_sources(
    user: User, config_path: Path
) -> None:
    config_path.write_text("stacks: []\n")
    await user.open("/")
    config_path.write_text(TWO_SOURCES)

    user.find(kind=ui.button, content="reload config").click()

    await user.should_see("First Source")


ONE_SOURCE = """
stacks:
  - id: stack_a
    name: Stack A
    sources:
      - id: usage_only
        name: Usage Only
        type: jsonplaceholder
"""


async def test_dashboard_shows_usage_of_a_source_without_billing(
    user: User, config_path: Path
) -> None:
    config_path.write_text(ONE_SOURCE)
    row = RowFactUsage(
        stack_id="stack_a",
        source_id="usage_only",
        source_type=SourceType.JSONPLACEHOLDER,
        extracted_at=datetime(2026, 11, 18, 12, 0, tzinfo=UTC),
        event_time=datetime(2026, 11, 17, tzinfo=UTC),
        usage_name="visitors",
        usage=84,
    )
    get_db().insert(TableName.FACT_USAGE, [row.model_dump()])

    await user.open("/")

    await user.should_see("No billing data available")
    await user.should_see("Usage (visitors)")


DOCKER_STACK = """
stacks:
  - id: stack_a
    name: Stack A
    sources:
      - id: lab
        name: Lab
        type: docker
        cost:
          hourly_cost: 1
        usage:
          type: beszel
          url: http://hub:8090
          email: me@example.com
          password: secret
"""


def pull_recorded_hub() -> None:
    """Pull the docker source of the stack from the recorded hub.

    The hub is only there during the pull, the page is opened after it.
    """
    with recorded_hub(get_http()) as usage:
        DockerService(
            get_db(),
            usage,
            "stack_a",
            "lab",
            [CostLine("Hosting", Decimal(1), Decimal(1), "hours")],
            lookback_days=1,
            now=lambda: datetime(2026, 11, 20, 15, tzinfo=UTC),
        ).fetch_source_data()


async def test_selfhosted_without_docker_data_says_what_to_do(
    user: User, config_path: Path
) -> None:
    config_path.write_text(DOCKER_STACK)

    await user.open("/selfhosted")

    await user.should_see("No Docker data yet")


async def test_selfhosted_shows_the_return_on_the_machine(
    user: User, config_path: Path
) -> None:
    config_path.write_text(DOCKER_STACK)
    pull_recorded_hub()

    await user.open("/selfhosted")

    await user.should_see("$730.00")  # the machine for 39 hours, as a month
    table = user.find(kind=ui.table).elements.pop()
    assert isinstance(table, ui.table)
    rows = cast(list[dict[str, str]], table.rows)
    assert rows[0]["app"] == "Elasticsearch"
    assert rows[0]["containers"] == "compose-lab-elastic-search-1"
    assert rows[0]["icon"] == "/ui-assets/icons/elasticsearch.svg"
