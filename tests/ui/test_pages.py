import asyncio
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
from varne.providers.types import RowDimSourceMeta, RowFactUsage


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
async def test_settings_form_shows_the_sources_of_the_file(
    user: User, config_path: Path
) -> None:
    config_path.write_text(TWO_SOURCES)
    await user.open("/settings")

    # the form is filled before it is opened
    inputs = user.find(kind=ui.input).elements
    assert {"first", "second", "third"} <= {str(i.value) for i in inputs}

    user.find(kind=ui.tab, content="Form").click()

    await user.should_see("Stack B")
    await user.should_see("Third Source")


async def test_settings_form_saves_to_the_file(user: User, config_path: Path) -> None:
    config_path.write_text(TWO_SOURCES)
    await user.open("/settings")
    user.find(kind=ui.tab, content="Form").click()
    await user.should_see("First Source")

    user.find(kind=ui.button, content="Save").click()

    await user.should_see("Configuration saved")
    assert "third" in config_path.read_text()


@pytest.mark.usefixtures("config_path")
async def test_sidebar_links_to_the_documentation(user: User) -> None:
    await user.open("/")

    await user.should_see("Documentation")
    link = user.find("Documentation").elements.pop()
    item = next(parent for parent in link.ancestors() if parent.props.get("href"))
    assert item.props["href"] == "https://www.narev.ai/docs/varne/v1/index"
    assert item.props["target"] == "_blank"


TWO_SOURCES = """
stacks:
  - id: stack_a
    name: Stack A
    sources:
      - id: first
        name: First Source
        type: anthropic
        api_token: secret
      - id: second
        name: Second Source
        type: anthropic
        api_token: secret
  - id: stack_b
    name: Stack B
    sources:
      - id: third
        name: Third Source
        type: anthropic
        api_token: secret
"""


async def test_dashboard_shows_a_card_for_every_source_of_the_stack(
    user: User, config_path: Path
) -> None:
    config_path.write_text(TWO_SOURCES)

    await user.open("/")

    await user.should_see("First Source")
    await user.should_see("Second Source")
    await user.should_not_see("Third Source")  # another stack


async def test_dashboard_reads_the_file_when_it_is_opened(
    user: User, config_path: Path
) -> None:
    config_path.write_text("stacks: []\n")
    await user.open("/")
    config_path.write_text(TWO_SOURCES)

    await user.open("/")

    await user.should_see("First Source")


async def test_dashboard_has_one_way_to_pull(user: User, config_path: Path) -> None:
    config_path.write_text(TWO_SOURCES)

    await user.open("/")

    await user.should_see("Pull all")
    table = user.find(kind=ui.table).elements.pop()
    assert isinstance(table, ui.table)
    statuses = [row["status"] for row in cast(list[dict[str, str]], table.rows)]
    assert statuses == ["Not pulled yet", "Not pulled yet"]
    await user.should_not_see("sync metadata")
    await user.should_not_see("reload config")


async def test_dashboard_marks_a_stored_source_that_is_not_in_the_file(
    user: User, config_path: Path
) -> None:
    config_path.write_text(TWO_SOURCES)
    get_db().insert(
        TableName.DIM_SOURCE_META,
        [
            RowDimSourceMeta(
                stack_id="stack_a",
                source_id="removed",
                source_type=SourceType.ANTHROPIC,
                extracted_at=datetime(2026, 11, 18, 12, tzinfo=UTC),
                value_name="x",
                value="y",
            ).model_dump()
        ],
    )

    await user.open("/")

    await user.should_see("First Source")
    table = user.find(kind=ui.table).elements.pop()
    assert isinstance(table, ui.table)
    rows = cast(list[dict[str, str | bool]], table.rows)
    assert [(row["id"], row["orphan"]) for row in rows] == [
        ("first", False),
        ("second", False),
        ("removed", True),
    ]
    assert rows[-1]["status"] == "Not in the configuration"


ONE_SOURCE = """
stacks:
  - id: stack_a
    name: Stack A
    sources:
      - id: usage_only
        name: Usage Only
        type: anthropic
        api_token: secret
"""


async def test_dashboard_shows_usage_of_a_source_without_billing(
    user: User, config_path: Path
) -> None:
    config_path.write_text(ONE_SOURCE)
    row = RowFactUsage(
        stack_id="stack_a",
        source_id="usage_only",
        source_type=SourceType.ANTHROPIC,
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


async def test_settings_form_locks_the_ids_of_saved_items(
    user: User, config_path: Path
) -> None:
    config_path.write_text(TWO_SOURCES)
    await user.open("/settings")

    ids = [i for i in user.find(kind=ui.input).elements if i.props.get("label") == "Id"]

    assert ids
    assert all("readonly" in i.props for i in ids)


async def test_settings_form_suggests_the_id_of_a_new_stack(
    user: User, config_path: Path
) -> None:
    config_path.write_text("stacks: []\n")
    await user.open("/settings")
    user.find(kind=ui.button, content="Add stack").click()
    await user.should_see("New stack")

    inputs = user.find(kind=ui.input).elements
    name_input = next(i for i in inputs if i.props.get("label") == "Name")
    id_input = next(i for i in inputs if i.props.get("label") == "Id")
    name_input.set_value("My Product 2")
    await user.should_see("My Product 2")
    await asyncio.sleep(0.3)  # bindings are refreshed on a timer

    assert id_input.value == "my_product_2"


async def test_dashboard_without_stacks_says_what_to_do(
    user: User, config_path: Path
) -> None:
    config_path.write_text("stacks: []\n")

    await user.open("/")

    await user.should_see("No stacks yet")
    await user.should_see("Open Settings")
    await user.should_see("Read the documentation")
    await user.should_not_see("Pull all")


async def test_selfhosted_without_stacks_says_what_to_do(
    user: User, config_path: Path
) -> None:
    config_path.write_text("stacks: []\n")

    await user.open("/selfhosted")

    await user.should_see("No stacks yet")


async def test_a_stack_without_sources_says_what_to_do(
    user: User, config_path: Path
) -> None:
    config_path.write_text("stacks:\n  - id: a\n    name: A\n")

    await user.open("/")

    await user.should_see("This stack has no sources")
