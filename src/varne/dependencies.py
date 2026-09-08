from functools import lru_cache

import httpx2 as httpx

from varne.config import ConfigManager, SourceId, StackId
from varne.db.connection import create_connection
from varne.db.schema import create_tables
from varne.db.types import DatabaseBackend
from varne.http import create_http_client
from varne.providers.base import ProviderService
from varne.providers.jsonplaceholder.client import JsonPlaceholderClient
from varne.providers.jsonplaceholder.service import JsonPlaceholderService
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


def get_json_placeholder_service(
    stack_id: StackId, source_id: SourceId
) -> ProviderService:
    return JsonPlaceholderService(
        db=get_db(),
        client=JsonPlaceholderClient(http=get_http()),
        stack_id=stack_id,
        source_id=source_id,
    )
