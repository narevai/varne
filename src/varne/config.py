import os
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, Field, SecretStr, ValidationError, model_validator

type SourceId = str


class SourceType(StrEnum):
    JSONPLACEHOLDER = "jsonplaceholder"
    VERCEL = "vercel"


class ConfigSourceBase(BaseModel):
    id: SourceId
    name: str


class ConfigJsonPlaceholder(ConfigSourceBase):
    type: Literal[SourceType.JSONPLACEHOLDER] = SourceType.JSONPLACEHOLDER


type VercelToken = SecretStr


class ConfigVercel(ConfigSourceBase):
    type: Literal[SourceType.VERCEL] = SourceType.VERCEL
    api_token: VercelToken | None = None
    api_token_env: str | None = None

    @model_validator(mode="after")
    def validate_token_source(self) -> ConfigVercel:
        if (self.api_token is None) == (self.api_token_env is None):
            raise ValueError(
                "Exactly one of api_token or api_token_env must be provided"
            )

        return self

    def get_api_token(self) -> VercelToken:
        if self.api_token is not None:
            return self.api_token

        assert self.api_token_env is not None

        value = os.getenv(self.api_token_env)

        if value is None:
            raise RuntimeError(
                f"Environment variable {self.api_token_env!r} is not set"
            )

        return SecretStr(value)


ConfigSource = Annotated[
    ConfigJsonPlaceholder | ConfigVercel, Field(discriminator="type")
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
