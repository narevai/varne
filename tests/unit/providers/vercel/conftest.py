import os
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import SecretStr

from varne.config import VercelToken


@pytest.fixture
def vercel_team_id() -> str:
    return "team_4lN90TlRlQzpFGhMLIoTTS9D"


@pytest.fixture
def vercel_project_id() -> str:
    return "prj_5LAip7eW0S0iDBoLNDwa9gMTye78"


# The recorded cassettes cover 2026-09-01 .. 2026-09-10: nine complete days before the 10th.
VERCEL_LOOKBACK_DAYS = 9


@pytest.fixture
def vercel_now() -> Callable[[], datetime]:
    return lambda: datetime(2026, 9, 10, 12, 30, tzinfo=UTC)


@pytest.fixture
def vercel_token() -> VercelToken:
    return SecretStr(os.getenv("VERCEL_TOKEN", "test-token"))


@pytest.fixture
def vcr_cassette_dir() -> str:
    return str(Path(__file__).parent / "cassettes")
