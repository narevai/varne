import os
from pathlib import Path

import pytest
from pydantic import SecretStr

from varne.config import BeszelPassword


@pytest.fixture
def beszel_url() -> str:
    return os.getenv("BESZEL_URL", "http://compose-lab:8090")


@pytest.fixture
def beszel_email() -> str:
    return os.getenv("BESZEL_EMAIL", "test@example.com")


@pytest.fixture
def beszel_password() -> BeszelPassword:
    return SecretStr(os.getenv("BESZEL_PASSWORD", "test-password"))


@pytest.fixture
def vcr_cassette_dir() -> str:
    return str(Path(__file__).parent / "cassettes")
