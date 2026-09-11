import os

import pytest
from pydantic import SecretStr

from varne.config import VercelToken


@pytest.fixture
def vercel_team_id() -> str:
    return "team_4lN90TlRlQzpFGhMLIoTTS9D"


@pytest.fixture
def vercel_project_id() -> str:
    return "prj_5LAip7eW0S0iDBoLNDwa9gMTye78"


@pytest.fixture
def vercel_token() -> VercelToken:
    return SecretStr(os.getenv("VERCEL_TOKEN", "test-token"))
