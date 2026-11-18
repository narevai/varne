import os
from pathlib import Path

import pytest
from pydantic import SecretStr

from varne.config import UmamiToken


@pytest.fixture
def umami_token() -> UmamiToken:
    return SecretStr(os.getenv("UMAMI_API_KEY", "test-token"))


@pytest.fixture
def umami_website_id() -> str:
    return "e7c44d9e-95fd-491e-b2ed-ea75b6916c3c"


@pytest.fixture
def vcr_cassette_dir() -> str:
    return str(Path(__file__).parent / "cassettes")
