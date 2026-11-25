from loguru import logger
from nicegui import run, ui

from varne.config import ConfigSource, ConfigStack
from varne.dependencies import get_service


async def sync_sources(stack: ConfigStack, sources: list[ConfigSource]) -> int:
    """Pull what the sources hold: their metadata and their data. Returns how many worked."""
    synced = 0
    for source in sources:
        service = get_service(stack_id=stack.id, source=source)

        try:
            await run.io_bound(service.fetch_source_meta)
            await run.io_bound(service.fetch_source_data)
            synced += 1
        except Exception as ex:
            message = f"Sync failed for {stack.name} / {source.name}: {ex}"
            logger.error(message)
            ui.notify(message, type="negative")
    return synced
