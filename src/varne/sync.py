from collections.abc import Sequence
from dataclasses import dataclass, field

from loguru import logger

from varne.config import ConfigSource, ConfigStack
from varne.dependencies import get_service


@dataclass(frozen=True)
class SyncFailure:
    source: ConfigSource
    message: str


@dataclass(frozen=True)
class SyncResult:
    synced: int = 0
    failures: list[SyncFailure] = field(default_factory=list)


def sync_sources(stack: ConfigStack, sources: Sequence[ConfigSource]) -> SyncResult:
    """Pull what the sources hold: their metadata and their data.

    A source that fails does not stop the others, it is reported in the result. This
    blocks until it is done, so a page runs it off its event loop.
    """
    synced = 0
    failures: list[SyncFailure] = []

    for source in sources:
        try:
            service = get_service(stack_id=stack.id, source=source)
            service.fetch_source_meta()
            service.fetch_source_data()
            synced += 1
        except Exception as exc:
            message = f"Sync failed for {stack.name} / {source.name}: {exc}"
            logger.error(message)
            failures.append(SyncFailure(source, message))

    return SyncResult(synced, failures)
