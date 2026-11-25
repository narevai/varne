from nicegui import run, ui

from varne.config import ConfigSource, ConfigStack
from varne.sync import sync_sources


async def sync_with_notice(stack: ConfigStack, sources: list[ConfigSource]) -> int:
    """Sync the sources off the event loop and say what failed. Returns how many worked."""
    result = await run.io_bound(sync_sources, stack, sources)

    for failure in result.failures:
        ui.notify(failure.message, type="negative")

    return result.synced
