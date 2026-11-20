from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import httpx2 as httpx

from varne.config import (
    ConfigAnthropic,
    ConfigBeszel,
    ConfigJsonPlaceholder,
    ConfigManager,
    ConfigOpenAI,
    ConfigSelfHosted,
    ConfigSource,
    ConfigUmami,
    ConfigVercel,
    StackId,
)
from varne.db.connection import create_connection
from varne.db.schema import create_tables
from varne.db.types import DatabaseBackend
from varne.http import create_http_client
from varne.providers.anthropic.client import AnthropicClient
from varne.providers.anthropic.service import AnthropicService
from varne.providers.base import ProviderService
from varne.providers.beszel.client import BeszelClient
from varne.providers.beszel.service import BeszelService
from varne.providers.jsonplaceholder.client import JsonPlaceholderClient
from varne.providers.jsonplaceholder.service import JsonPlaceholderService
from varne.providers.openai.client import OpenAIClient
from varne.providers.openai.service import OpenAIService
from varne.providers.selfhosted.rates import cost_lines
from varne.providers.selfhosted.service import SelfHostedService
from varne.providers.umami.client import UmamiClient
from varne.providers.umami.service import UmamiService
from varne.providers.vercel.client import VercelClient
from varne.providers.vercel.service import VercelService
from varne.settings import get_settings

if TYPE_CHECKING:
    from varne.cassettes import CassetteManager


@lru_cache
def get_db() -> DatabaseBackend:
    settings = get_settings()

    db = create_connection(settings.database_path)
    create_tables(db)

    return db


@lru_cache
def get_http() -> httpx.Client:
    return create_http_client()


@lru_cache
def get_config_manager() -> ConfigManager:
    settings = get_settings()

    manager = ConfigManager(path=settings.config_path)
    manager.load()

    return manager


@lru_cache
def get_cassette_manager() -> CassetteManager:
    from varne.cassettes import CassetteManager

    return CassetteManager(
        cassette_paths=list(Path("tests/unit/providers").glob("**/cassettes/**/*.yaml"))
    )


def get_service(stack_id: StackId, source: ConfigSource) -> ProviderService:
    match source:
        case ConfigJsonPlaceholder():
            return JsonPlaceholderService(
                db=get_db(),
                client=JsonPlaceholderClient(http=get_http()),
                stack_id=stack_id,
                source_id=source.id,
            )
        case ConfigVercel():
            return VercelService(
                db=get_db(),
                client=VercelClient(http=get_http(), api_token=source.get_api_token()),
                stack_id=stack_id,
                source_id=source.id,
                team_id=source.team_id,
                project_ids=source.project_ids,
                lookback_days=source.lookback_days,
            )
        case ConfigAnthropic():
            return AnthropicService(
                db=get_db(),
                client=AnthropicClient(
                    http=get_http(), api_token=source.get_api_token()
                ),
                stack_id=stack_id,
                source_id=source.id,
                lookback_days=source.lookback_days,
            )
        case ConfigUmami():
            return UmamiService(
                db=get_db(),
                client=UmamiClient(http=get_http(), api_token=source.get_api_token()),
                stack_id=stack_id,
                source_id=source.id,
                website_ids=source.website_ids,
                lookback_days=source.lookback_days,
            )
        case ConfigOpenAI():
            return OpenAIService(
                db=get_db(),
                client=OpenAIClient(http=get_http(), api_token=source.get_api_token()),
                stack_id=stack_id,
                source_id=source.id,
                lookback_days=source.lookback_days,
            )
        case ConfigSelfHosted():
            return SelfHostedService(
                db=get_db(),
                stack_id=stack_id,
                source_id=source.id,
                lines=cost_lines(
                    hourly_cost=source.hourly_cost,
                    machine_cost=source.machine_cost,
                    amortization_years=source.amortization_years,
                    power_draw_watts=source.power_draw_watts,
                    electricity_price_per_kwh=source.electricity_price_per_kwh,
                ),
                lookback_days=source.lookback_days,
            )
        case ConfigBeszel():
            return BeszelService(
                db=get_db(),
                client=BeszelClient(
                    http=get_http(),
                    url=source.url,
                    email=source.email,
                    password=source.get_password(),
                ),
                stack_id=stack_id,
                source_id=source.id,
                lookback_days=source.lookback_days,
            )
