import pytest
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
