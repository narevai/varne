from pathlib import Path

from nicegui.testing import User


async def test_page_dashboard(user: User, config_path: Path) -> None:
    await user.open("/")
    await user.should_see("Dashboard")
