from pathlib import Path

import pytest
from nicegui import ui
from nicegui.testing import User


@pytest.mark.usefixtures("config_path")
async def test_page_dashboard(user: User) -> None:
    await user.open("/")
    await user.should_see("Dashboard")


@pytest.mark.usefixtures("config_path")
async def test_page_settings(user: User) -> None:
    await user.open("/settings")
    await user.should_see("Settings")
    await user.should_see("stack_test")


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
