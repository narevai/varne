from typing import cast

import pandas as pd
from loguru import logger
from nicegui import run, ui

from varne.analytics.usage import get_usage_by_id
from varne.db.types import DatabaseBackend
from varne.dependencies import get_config_manager, get_db, get_json_placeholder_service
from varne.ui.layout import create_layout


def get_usage_rows(db: DatabaseBackend) -> list[dict[str, object]]:
    result = cast(pd.DataFrame, get_usage_by_id(db).execute())
    rows = result.to_dict(orient="records")  # pyright: ignore[reportUnknownVariableType]

    return cast(list[dict[str, object]], rows)


@ui.page("/")
async def page_dashboard() -> None:
    layout = create_layout()
    db = get_db()
    config_manager = get_config_manager()

    with layout:
        ui.label("Dashboard").classes("text-2xl font-bold")
        if config_manager.config is not None:
            stack_names = [stack.name for stack in config_manager.config.stacks]
            stack_select = ui.select(
                options=stack_names, label="stack", value=stack_names[0]
            )
        else:
            ui.label("no stacks found, define in Settings")
        columns = [
            {
                "name": "id",
                "label": "ID",
                "field": "id",
                "align": "left",
            },
            {
                "name": "total_amount",
                "label": "Total Amount",
                "field": "total_amount",
                "align": "right",
            },
        ]
        table = ui.table(
            columns=columns,
            rows=[],
            row_key="id",
        )

        async def refresh_table() -> None:
            rows = await run.io_bound(get_usage_rows, db)
            table.rows = rows or []

        async def sync_usage() -> None:
            service = get_json_placeholder_service()

            button.disable()

            try:
                _ = await run.io_bound(service.fetch_and_store)
                await refresh_table()
                ui.notify("Synced rows")

            except Exception as ex:
                logger.error(f"Sync failed {ex}")
                ui.notify("Sync failed.", type="negative")

            finally:
                button.enable()

        button = ui.button("sync", on_click=sync_usage)
        await refresh_table()
