from pathlib import Path
from typing import cast

import ibis
from loguru import logger

from varne.db.types import DatabaseBackend


def create_connection(path_db: str | Path) -> DatabaseBackend:
    logger.debug(
        f"Connecting to DuckDB at {path_db}",
    )
    database_path = Path(path_db)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return cast(DatabaseBackend, ibis.connect(database_path))
