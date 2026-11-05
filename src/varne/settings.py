from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", extra="ignore"
    )

    environment: str = "development"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    log_level: str = "INFO"

    api_title: str = "Varne"
    api_description: str = "Varne API"
    api_version: str = "1.0.0-alpha.0"

    database_path: str = "./data/app.duckdb"
    config_path: str = "./config/varne.yaml"

    static_path: Path = Field(
        default_factory=lambda: Path(str(files("varne.ui") / "static"))
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
