from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError


class ConfigSourceBase(BaseModel):
    id: str
    name: str


class ConfigJsonPlaceholder(ConfigSourceBase):
    type: Literal["jsonplaceholder"] = "jsonplaceholder"


ConfigSource = Annotated[ConfigJsonPlaceholder, Field(discriminator="type")]


class ConfigStack(BaseModel):
    id: str
    name: str
    sources: list[ConfigSource] = Field(default_factory=list)


class ConfigVarne(BaseModel):
    stacks: list[ConfigStack]


class ConfigManager:
    def __init__(self, path: Path | str):
        self.path: Path = Path(path)
        self.config: ConfigVarne | None = None
        self.error: str | None = None

    def load(self) -> ConfigVarne:
        try:
            raw = yaml.safe_load(self.path.read_text())  # pyright: ignore[reportAny]
            self.config = ConfigVarne.model_validate(raw or {})
        except yaml.YAMLError as exc:
            self.error = str(exc)
            self.config = ConfigVarne(stacks=[])
        except ValidationError as exc:
            error = exc.errors()[0]
            self.error = f"{'.'.join(map(str, error['loc']))}: {error['msg']}"
            self.config = ConfigVarne(stacks=[])
        return self.config

    def save(self):

        if self.config is None:
            config_current = ConfigVarne(stacks=[]).model_dump(
                mode="json", exclude_none=True
            )
        else:
            config_current = self.config.model_dump(mode="json", exclude_none=True)

        config_tmp_path = self.path.with_suffix(".tmp")
        config_tmp = yaml.safe_dump(config_current, sort_keys=False)
        config_tmp_path.write_text(config_tmp)

        config_tmp_path.replace(self.path)
