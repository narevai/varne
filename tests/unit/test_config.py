from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from varne.config import ConfigManager, ConfigVarne, SourceType


@pytest.fixture
def config_single_jsonplaceholder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "config" / "varne.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        """
stacks:
  - id: stack_id1
    name: stack1

    sources:
      - id: source1
        name: Source 1
        type: jsonplaceholder

"""
    )

    return path


@pytest.fixture
def config_single_vercel_token_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "config" / "varne.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        """
stacks:
  - id: stack_id1
    name: stack1

    sources:
      - id: vercel1
        name: Vercel 1
        type: vercel
"""
    )

    return path


@pytest.fixture
def config_single_vercel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "config" / "varne.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        """
stacks:
  - id: stack_id1
    name: stack1

    sources:
      - id: vercel1
        name: Vercel 1
        type: vercel
        api_token: testtoken
"""
    )

    return path


def test_jsonplaceholder_load(config_single_jsonplaceholder: Path):
    raw = yaml.safe_load(config_single_jsonplaceholder.read_text())  # pyright: ignore[reportAny]
    config = ConfigVarne.model_validate(raw or {})

    assert config.stacks != []
    assert config.stacks[0].id == "stack_id1"
    assert config.stacks[0].name == "stack1"
    assert config.stacks[0].sources != []
    assert config.stacks[0].sources[0].id == "source1"
    assert config.stacks[0].sources[0].name == "Source 1"
    assert config.stacks[0].sources[0].type == SourceType.JSONPLACEHOLDER


def test_config_json_placeholder(config_single_jsonplaceholder: Path):
    manager = ConfigManager(path=config_single_jsonplaceholder)
    manager.load()

    config = manager.config

    assert config is not None
    assert config.stacks != []
    assert config.stacks[0].id == "stack_id1"
    assert config.stacks[0].name == "stack1"
    assert config.stacks[0].sources != []
    assert config.stacks[0].sources[0].id == "source1"
    assert config.stacks[0].sources[0].name == "Source 1"
    assert config.stacks[0].sources[0].type == SourceType.JSONPLACEHOLDER


def test_vercel_load_token_missing(config_single_vercel_token_missing: Path):
    raw = yaml.safe_load(config_single_vercel_token_missing.read_text())  # pyright: ignore[reportAny]

    with pytest.raises(
        ValidationError,
        match="Exactly one of api_token or api_token_env must be provided",
    ):
        ConfigVarne.model_validate(raw or {})


def test_config_vercel(config_single_vercel: Path):
    manager = ConfigManager(path=config_single_vercel)
    manager.load()

    config = manager.config

    assert config is not None
    assert config.stacks != []
    assert config.stacks[0].id == "stack_id1"
    assert config.stacks[0].name == "stack1"
    assert config.stacks[0].sources != []
    assert config.stacks[0].sources[0].id == "vercel1"
    assert config.stacks[0].sources[0].name == "Vercel 1"
    assert config.stacks[0].sources[0].type == SourceType.VERCEL
