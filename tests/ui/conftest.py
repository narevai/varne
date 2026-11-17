import pytest

from varne.dependencies import get_config_manager, get_db, get_http
from varne.settings import get_settings


@pytest.fixture(autouse=True)
def fresh_app_state():
    """The app caches its config manager and database; every UI test starts clean."""
    for cached in (get_config_manager, get_db, get_http, get_settings):
        cached.cache_clear()
    yield
    for cached in (get_config_manager, get_db, get_http, get_settings):
        cached.cache_clear()
