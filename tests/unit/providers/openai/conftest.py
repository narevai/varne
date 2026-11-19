import os
from pathlib import Path

import pytest
from pydantic import SecretStr

from varne.config import OpenAIToken


@pytest.fixture
def openai_token() -> OpenAIToken:
    return SecretStr(os.getenv("OPENAI_ADMIN_KEY", "test-token"))


@pytest.fixture
def vcr_cassette_dir() -> str:
    return str(Path(__file__).parent / "cassettes")
