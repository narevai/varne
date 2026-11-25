from pathlib import Path

from loguru import logger

from varne.config import ConfigDocker
from varne.db.sources import stored_source_ids
from varne.demo import DEMO_CONFIG, DEMO_STACK_ID


def reset_demo(config_path: Path, database_path: Path) -> None:
    """Start the demo from its sample, whatever was done to it since the last start.

    Anyone who opens a demo can change its configuration or delete its data. A
    restart puts both back, so a demo that was broken is not broken for good.
    """
    for leftover in (
        database_path,
        database_path.with_name(database_path.name + ".wal"),
    ):
        leftover.unlink(missing_ok=True)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(DEMO_CONFIG)


def seed_demo() -> None:
    """Sync the sample source once, so that the demo opens on real looking data.

    It runs after the app is up, and not again when the demo has its data.
    """
    # imported here, the dependencies need the settings, which need this package
    from varne.dependencies import get_config_manager, get_db
    from varne.sync import sync_sources

    config = get_config_manager().load()
    stack = next((x for x in config.stacks if x.id == DEMO_STACK_ID), None)
    if stack is None or stored_source_ids(get_db(), stack.id):
        return

    sources = [x for x in stack.sources if isinstance(x, ConfigDocker)]
    result = sync_sources(stack, sources)
    logger.info(f"Demo data ready for {result.synced} of {len(sources)} source(s)")
