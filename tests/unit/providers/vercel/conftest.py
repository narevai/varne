import os

import pytest

from varne.config import VercelToken


@pytest.fixture
def vercel_team_id() -> str:
    return "team_4lN90TlRlQzpFGhMLIoTTS9D"


@pytest.fixture
def vercel_token() -> VercelToken:
    return os.getenv("VERCEL_TOKEN", "test-token")
