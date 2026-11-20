from decimal import Decimal
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from varne.config import (
    DEFAULT_LOOKBACK_DAYS,
    ConfigAnthropic,
    ConfigBeszel,
    ConfigManager,
    ConfigOpenAI,
    ConfigSelfHosted,
    ConfigUmami,
    ConfigVarne,
    SourceType,
    parse_config,
)


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
        team_id: team_test
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
        team_id: team_test
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


def test_config_save_text_valid(config_single_jsonplaceholder: Path):
    manager = ConfigManager(path=config_single_jsonplaceholder)
    manager.load()

    text = "# my comment\nstacks:\n  - id: stack_new\n    name: New\n"
    error = manager.save_text(text)

    assert error is None
    assert config_single_jsonplaceholder.read_text() == text
    assert manager.config is not None
    assert manager.config.stacks[0].id == "stack_new"
    assert manager.error is None


def test_config_save_text_invalid_keeps_file(config_single_jsonplaceholder: Path):
    manager = ConfigManager(path=config_single_jsonplaceholder)
    manager.load()
    before = config_single_jsonplaceholder.read_text()

    error = manager.save_text("stacks:\n  - id: stack_new\n")

    assert error == "stacks.0.name: Field required"
    assert config_single_jsonplaceholder.read_text() == before
    assert manager.config is not None
    assert manager.config.stacks[0].id == "stack_id1"


def test_config_missing_file_is_created_empty(tmp_path: Path):
    path = tmp_path / "does" / "not" / "exist" / "varne.yaml"
    manager = ConfigManager(path=path)

    config = manager.load()

    assert manager.error is None
    assert config.stacks == []
    assert path.read_text() == "stacks: []\n"


def test_config_missing_file_not_creatable_reports_error(tmp_path: Path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    manager = ConfigManager(path=blocker / "varne.yaml")

    config = manager.load()

    assert manager.error is not None
    assert config.stacks == []


def test_config_existing_file_is_not_overwritten(config_single_jsonplaceholder: Path):
    before = config_single_jsonplaceholder.read_text()
    ConfigManager(path=config_single_jsonplaceholder).load()
    assert config_single_jsonplaceholder.read_text() == before


def test_vercel_source_needs_a_team_id():
    from pydantic import SecretStr

    from varne.config import ConfigVercel

    with pytest.raises(ValidationError):
        ConfigVercel(id="v", name="V", api_token=SecretStr("x"))  # pyright: ignore[reportCallIssue]


def test_vercel_source_defaults():
    from pydantic import SecretStr

    from varne.config import ConfigVercel

    source = ConfigVercel(id="v", name="V", api_token=SecretStr("x"), team_id="team_1")

    assert source.project_ids == []
    assert source.lookback_days == 30


def test_vercel_source_reads_team_and_projects_from_yaml():
    from varne.config import ConfigVercel, parse_config

    config = parse_config(
        """
stacks:
  - id: s
    name: S
    sources:
      - id: v
        name: V
        type: vercel
        api_token: abc
        team_id: team_1
        project_ids: [prj_a, prj_b]
        lookback_days: 7
"""
    )
    source = config.stacks[0].sources[0]

    assert isinstance(source, ConfigVercel)
    assert source.team_id == "team_1"
    assert source.project_ids == ["prj_a", "prj_b"]
    assert source.lookback_days == 7


def test_old_vercel_config_without_team_id_gives_a_readable_error():
    from varne.config import parse_config

    with pytest.raises(ValueError, match="team_id"):
        parse_config(
            """
stacks:
  - id: s
    name: S
    sources:
      - id: v
        name: V
        type: vercel
        api_token: abc
"""
        )


def test_config_reads_anthropic_source():
    config = parse_config(
        """
stacks:
  - id: s
    name: S
    sources:
      - id: a
        name: A
        type: anthropic
        api_token: sk-ant-admin-x
"""
    )
    source = config.stacks[0].sources[0]

    assert isinstance(source, ConfigAnthropic)
    assert source.lookback_days == 30
    assert source.get_api_token().get_secret_value() == "sk-ant-admin-x"


def test_config_anthropic_needs_exactly_one_token_source():
    with pytest.raises(ValueError, match="Exactly one of api_token"):
        parse_config(
            """
stacks:
  - id: s
    name: S
    sources:
      - id: a
        name: A
        type: anthropic
"""
        )


def test_config_reads_openai_source():
    config = parse_config(
        """
stacks:
  - id: s
    name: S
    sources:
      - id: o
        name: O
        type: openai
        api_token: sk-admin-x
"""
    )
    source = config.stacks[0].sources[0]

    assert isinstance(source, ConfigOpenAI)
    assert source.lookback_days == 30
    assert source.get_api_token().get_secret_value() == "sk-admin-x"


def test_config_openai_needs_exactly_one_token_source():
    with pytest.raises(ValueError, match="Exactly one of api_token"):
        parse_config(
            """
stacks:
  - id: s
    name: S
    sources:
      - id: o
        name: O
        type: openai
"""
        )


def test_config_reads_umami_source():
    config = parse_config(
        """
stacks:
  - id: s
    name: S
    sources:
      - id: u
        name: U
        type: umami
        api_token: key
        website_ids: [w1]
"""
    )
    source = config.stacks[0].sources[0]

    assert isinstance(source, ConfigUmami)
    assert source.website_ids == ["w1"]
    assert source.lookback_days == 30


def test_config_umami_needs_a_website():
    with pytest.raises(ValueError, match="website_ids"):
        parse_config(
            """
stacks:
  - id: s
    name: S
    sources:
      - id: u
        name: U
        type: umami
        api_token: key
        website_ids: []
"""
        )


def selfhosted(fields: str) -> str:
    return f"""
stacks:
  - id: s
    name: S
    sources:
      - id: lab
        name: Lab
        type: selfhosted
{fields}
"""


def test_selfhosted_machine_cost_with_electricity():
    config = parse_config(
        selfhosted(
            "\n".join(
                [
                    "        machine_cost: 5000",
                    "        power_draw_watts: 120",
                    "        electricity_price_per_kwh: 0.9",
                ]
            )
        )
    )
    source = config.stacks[0].sources[0]

    assert isinstance(source, ConfigSelfHosted)
    assert source.machine_cost == 5000
    assert source.amortization_years == 6
    assert source.power_draw_watts == 120
    assert source.electricity_price_per_kwh == Decimal("0.9")
    assert source.lookback_days == 30


def test_selfhosted_hourly_cost():
    config = parse_config(selfhosted("        hourly_cost: 0.35"))
    source = config.stacks[0].sources[0]

    assert isinstance(source, ConfigSelfHosted)
    assert source.hourly_cost == Decimal("0.35")


def test_selfhosted_amortization_years_can_be_changed():
    config = parse_config(
        selfhosted("        machine_cost: 5000\n        amortization_years: 4")
    )
    source = config.stacks[0].sources[0]

    assert isinstance(source, ConfigSelfHosted)
    assert source.amortization_years == 4


@pytest.mark.parametrize(
    "fields",
    [
        "        lookback_days: 7",
        "        machine_cost: 5000\n        hourly_cost: 0.35",
    ],
)
def test_selfhosted_needs_exactly_one_of_machine_cost_and_hourly_cost(fields: str):
    with pytest.raises(ValueError, match="Exactly one of hourly_cost or machine_cost"):
        parse_config(selfhosted(fields))


@pytest.mark.parametrize(
    "fields",
    [
        "        machine_cost: 5000\n        power_draw_watts: 120",
        "        machine_cost: 5000\n        electricity_price_per_kwh: 0.9",
    ],
)
def test_selfhosted_power_and_electricity_price_come_together(fields: str):
    with pytest.raises(ValueError, match="must be provided together"):
        parse_config(selfhosted(fields))


@pytest.mark.parametrize(
    "extra",
    [
        "        amortization_years: 6",
        "        power_draw_watts: 120\n        electricity_price_per_kwh: 0.9",
    ],
)
def test_selfhosted_hourly_cost_excludes_the_hardware_options(extra: str):
    with pytest.raises(ValueError, match="cannot be used with hourly_cost"):
        parse_config(selfhosted("        hourly_cost: 0.35\n" + extra))


@pytest.mark.parametrize("value", ["0", "-5"])
def test_selfhosted_costs_must_be_positive(value: str):
    with pytest.raises(ValueError, match="greater than 0"):
        parse_config(selfhosted(f"        machine_cost: {value}"))


def test_beszel_source_uses_the_default_lookback():
    config = parse_config(
        """
stacks:
  - id: s
    name: S
    sources:
      - id: b
        name: Beszel
        type: beszel
        url: http://hub:8090
        email: me@example.com
        password: secret
"""
    )

    source = config.stacks[0].sources[0]
    assert isinstance(source, ConfigBeszel)
    assert source.lookback_days == DEFAULT_LOOKBACK_DAYS
    assert source.get_password().get_secret_value() == "secret"


def test_beszel_password_comes_from_exactly_one_place():
    text = """
stacks:
  - id: s
    name: S
    sources:
      - id: b
        name: Beszel
        type: beszel
        url: http://hub:8090
        email: me@example.com
"""

    with pytest.raises(ValueError, match="Exactly one of password or password_env"):
        parse_config(text)

    with pytest.raises(ValueError, match="Exactly one of password or password_env"):
        parse_config(text + "        password: a\n        password_env: B\n")
