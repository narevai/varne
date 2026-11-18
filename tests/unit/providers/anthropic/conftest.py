import os
from pathlib import Path

import pytest
from pydantic import SecretStr

from varne.config import AnthropicToken


@pytest.fixture
def anthropic_token() -> AnthropicToken:
    return SecretStr(os.getenv("ANTHROPIC_ADMIN_KEY", "test-token"))


@pytest.fixture
def vcr_cassette_dir() -> str:
    return str(Path(__file__).parent / "cassettes")
