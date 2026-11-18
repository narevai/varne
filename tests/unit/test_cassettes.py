from pathlib import Path

import pytest

from varne.cassettes import CassetteManager
from varne.http import create_http_client

VERCEL_CASSETTES = Path(__file__).parent / "providers" / "vercel" / "cassettes"


@pytest.fixture
def manager():
    manager = CassetteManager(sorted(VERCEL_CASSETTES.glob("*.yaml")))
    manager.start()
    yield manager
    manager.stop()


@pytest.mark.usefixtures("manager")
def test_recorded_response_is_played_for_another_team_and_period():
    with create_http_client() as http:
        response = http.get(
            "https://api.vercel.com/v1/billing/charges",
            params={"teamId": "team_someone_else", "from": "2030-01-01T00:00:00Z"},
        )

    assert response.is_success


@pytest.mark.usefixtures("manager")
def test_unknown_path_is_not_played():
    with (
        create_http_client() as http,
        pytest.raises(Exception, match="No match for the request"),
    ):
        http.get("https://api.vercel.com/v1/nothing-recorded")
