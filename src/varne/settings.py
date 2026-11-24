from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import ClassVar, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", extra="ignore"
    )

    environment: str = "production"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    log_level: str = "INFO"

    api_title: str = "Varne"
    api_description: str = "Varne API"
    api_version: str = "1.0.0-alpha.0"

    database_path: str = "./data/app.duckdb"
    config_path: str = "./config/varne.yaml"

    # Anonymous "server started" event, see telemetry.py.
    enable_telemetry: bool = True
    umami_host: str = "https://cloud.umami.is"
    umami_website_id: str = "845ce56d-b618-400b-8e4b-b40353659bb6"

    # A sample stack on a database and a configuration of its own, so that nothing
    # of yours is touched. It is filled in once the app is up, see demo/seed.py.
    demo_mode: bool = False

    static_path: Path = Field(
        default_factory=lambda: Path(str(files("varne.ui") / "static"))
    )

    @model_validator(mode="after")
    def use_the_demo_files(self) -> Self:
        if self.demo_mode:
            self.database_path = str(Path(self.database_path).with_name("demo.duckdb"))
            self.config_path = str(Path(self.config_path).with_name("demo.yaml"))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
