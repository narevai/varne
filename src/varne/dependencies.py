from functools import lru_cache
from pathlib import Path

import httpx2 as httpx

from varne.cassettes import CassetteManager
from varne.config import (
    ConfigJsonPlaceholder,
    ConfigManager,
    ConfigSource,
    ConfigVercel,
    StackId,
)
from varne.db.connection import create_connection
from varne.db.schema import create_tables
from varne.db.types import DatabaseBackend
from varne.http import create_http_client
from varne.providers.base import ProviderService
from varne.providers.jsonplaceholder.client import JsonPlaceholderClient
from varne.providers.jsonplaceholder.service import JsonPlaceholderService
from varne.providers.vercel.client import VercelClient
from varne.providers.vercel.service import VercelService
from varne.settings import get_settings


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
    return CassetteManager(
        cassette_paths=[
            Path(
                "tests/unit/providers/jsonplaceholder/cassettes/test_client/test_fetch.yaml"
            ),
            Path(
                "tests/unit/providers/jsonplaceholder/cassettes/test_service/test_store.yaml"
            ),
            Path(
                "tests/unit/providers/vercel/cassettes/test_client_projects/test_fetch_projects.yaml"
            ),
            Path(
                "tests/unit/providers/vercel/cassettes/test_client_billing/test_fetch_billing.yaml"
            ),
            Path(
                "tests/unit/providers/vercel/cassettes/test_client_web_analytics_visits_aggregate/test_fetch_web_analytics_visits_aggregate.yaml"
            ),
            Path(
                "tests/unit/providers/vercel/cassettes/test_client_web_analytics_visits_count/test_fetch_web_analytics_visits_count.yaml"
            ),
        ]
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
            )
