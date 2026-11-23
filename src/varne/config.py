import os
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

import yaml
from pydantic import BaseModel, Field, SecretStr, ValidationError, model_validator

type SourceId = str


class SourceType(StrEnum):
    ANTHROPIC = "anthropic"
    DOCKER = "docker"
    JSONPLACEHOLDER = "jsonplaceholder"
    OPENAI = "openai"
    UMAMI = "umami"
    VERCEL = "vercel"


class ConfigSourceBase(BaseModel):
    id: SourceId
    name: str


class ConfigJsonPlaceholder(ConfigSourceBase):
    type: Literal[SourceType.JSONPLACEHOLDER] = SourceType.JSONPLACEHOLDER


DEFAULT_LOOKBACK_DAYS = 30


class ConfigLookbackSource(ConfigSourceBase):
    lookback_days: int = Field(default=DEFAULT_LOOKBACK_DAYS, ge=1, le=365)


class ConfigApiSource(ConfigLookbackSource):
    api_token: SecretStr | None = None
    api_token_env: str | None = None

    @model_validator(mode="after")
    def validate_token_source(self) -> Self:
        if (self.api_token is None) == (self.api_token_env is None):
            raise ValueError(
                "Exactly one of api_token or api_token_env must be provided"
            )

        return self

    def get_api_token(self) -> SecretStr:
        if self.api_token is not None:
            return self.api_token

        assert self.api_token_env is not None

        value = os.getenv(self.api_token_env)

        if value is None:
            raise RuntimeError(
                f"Environment variable {self.api_token_env!r} is not set"
            )

        return SecretStr(value)


type VercelToken = SecretStr


class ConfigVercel(ConfigApiSource):
    type: Literal[SourceType.VERCEL] = SourceType.VERCEL
    team_id: str = Field(min_length=1)
    project_ids: list[str] = Field(default_factory=list)


type AnthropicToken = SecretStr


class ConfigAnthropic(ConfigApiSource):
    type: Literal[SourceType.ANTHROPIC] = SourceType.ANTHROPIC


type OpenAIToken = SecretStr


class ConfigOpenAI(ConfigApiSource):
    type: Literal[SourceType.OPENAI] = SourceType.OPENAI


type UmamiToken = SecretStr


class ConfigUmami(ConfigApiSource):
    type: Literal[SourceType.UMAMI] = SourceType.UMAMI
    website_ids: list[str] = Field(min_length=1)


class ConfigDockerCost(BaseModel):
    """What the machine costs: a rented hourly rate, or hardware plus power."""

    hourly_cost: Decimal | None = Field(default=None, gt=0)
    machine_cost: Decimal | None = Field(default=None, gt=0)
    amortization_years: Decimal = Field(default=Decimal(6), gt=0, le=50)
    power_draw_watts: Decimal | None = Field(default=None, gt=0)
    electricity_price_per_kwh: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_cost_mode(self) -> Self:
        if (self.hourly_cost is None) == (self.machine_cost is None):
            raise ValueError(
                "Exactly one of hourly_cost or machine_cost must be provided"
            )

        if (self.power_draw_watts is None) != (self.electricity_price_per_kwh is None):
            raise ValueError(
                "power_draw_watts and electricity_price_per_kwh must be provided together"
            )

        if self.hourly_cost is not None:
            hardware_only = {
                "amortization_years",
                "power_draw_watts",
                "electricity_price_per_kwh",
            }
            if hardware_only & self.model_fields_set:
                raise ValueError(
                    "amortization_years, power_draw_watts and electricity_price_per_kwh cannot be used with hourly_cost"
                )

        return self


type BeszelPassword = SecretStr


class ConfigBeszelUsage(BaseModel):
    type: Literal["beszel"] = "beszel"
    url: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: SecretStr | None = None
    password_env: str | None = None

    @model_validator(mode="after")
    def validate_password_source(self) -> Self:
        if (self.password is None) == (self.password_env is None):
            raise ValueError("Exactly one of password or password_env must be provided")

        return self

    def get_password(self) -> BeszelPassword:
        if self.password is not None:
            return self.password

        assert self.password_env is not None

        value = os.getenv(self.password_env)

        if value is None:
            raise RuntimeError(f"Environment variable {self.password_env!r} is not set")

        return SecretStr(value)


ConfigDockerUsage = Annotated[ConfigBeszelUsage, Field(discriminator="type")]


class ConfigDocker(ConfigLookbackSource):
    type: Literal[SourceType.DOCKER] = SourceType.DOCKER
    cost: ConfigDockerCost
    usage: ConfigDockerUsage


ConfigSource = Annotated[
    ConfigJsonPlaceholder
    | ConfigVercel
    | ConfigAnthropic
    | ConfigDocker
    | ConfigOpenAI
    | ConfigUmami,
    Field(discriminator="type"),
]

type StackId = str


class ConfigStack(BaseModel):
    id: StackId
    name: str
    sources: list[ConfigSource] = Field(default_factory=list)


class ConfigVarne(BaseModel):
    stacks: list[ConfigStack]


EMPTY_CONFIG_TEXT = "stacks: []\n"


def parse_config(text: str) -> ConfigVarne:
    try:
        raw = yaml.safe_load(text)  # pyright: ignore[reportAny]
        return ConfigVarne.model_validate(raw or {})
    except yaml.YAMLError as exc:
        raise ValueError(str(exc)) from exc
    except ValidationError as exc:
        error = exc.errors()[0]
        raise ValueError(f"{'.'.join(map(str, error['loc']))}: {error['msg']}") from exc


class ConfigManager:
    def __init__(self, path: Path | str):
        self.path: Path = Path(path)
        self.config: ConfigVarne | None = None
        self.error: str | None = None

    def _ensure_file(self) -> None:
        """Create an empty config on first start so the file always exists."""
        if self.path.exists():
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(EMPTY_CONFIG_TEXT)

    def load(self) -> ConfigVarne:
        try:
            self._ensure_file()
            self.config = parse_config(self.path.read_text())
            self.error = None
        except (ValueError, OSError) as exc:
            self.error = str(exc)
            self.config = ConfigVarne(stacks=[])
        return self.config

    def save_text(self, text: str) -> str | None:
        try:
            parse_config(text)
        except ValueError as exc:
            return str(exc)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        config_tmp_path = self.path.with_suffix(".tmp")
        config_tmp_path.write_text(text)
        config_tmp_path.replace(self.path)

        self.load()
        return None

    def save(self):

        if self.config is None:
            config_current = ConfigVarne(stacks=[]).model_dump(
                mode="json", exclude_none=True
            )
        else:
            config_current = self.config.model_dump(mode="json", exclude_none=True)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        config_tmp_path = self.path.with_suffix(".tmp")
        config_tmp = yaml.safe_dump(config_current, sort_keys=False)
        config_tmp_path.write_text(config_tmp)

        config_tmp_path.replace(self.path)
