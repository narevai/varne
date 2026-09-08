from typing import cast

import pandas as pd
from loguru import logger
from nicegui import run, ui
from nicegui.elements.select import Select

from varne.analytics.usage import get_usage_by_id
from varne.config import ConfigVarne, StackId
from varne.db.types import DatabaseBackend
from varne.dependencies import get_config_manager, get_db, get_json_placeholder_service
from varne.ui.layout import create_layout


def get_usage_rows(db: DatabaseBackend, stack_id: StackId) -> list[dict[str, object]]:
    result = cast(pd.DataFrame, get_usage_by_id(db, stack_id).execute())
    rows = result.to_dict(orient="records")  # pyright: ignore[reportUnknownVariableType]

    return cast(list[dict[str, object]], rows)


def create_stack_select(config: ConfigVarne | None) -> Select:
    if config is None or not config.stacks:
        return ui.select(options={}, label="stack", value=None)

    stack_options = {stack.id: stack.name for stack in config.stacks}

    return ui.select(options=stack_options, label="stack", value=config.stacks[0].id)


def refresh_stack_select(select: Select, config: ConfigVarne):
    select.options = {stack.id: stack.name for stack in config.stacks}
    select.value = config.stacks[0].id
    select.update()


@ui.page("/")
async def page_dashboard() -> None:
    layout = create_layout()
    db = get_db()
    config_manager = get_config_manager()

    with layout:
        ui.label("Dashboard").classes("text-2xl font-bold")

        if config_manager.config is None or not config_manager.config.stacks:
            ui.label("No stacks found, define in Settings")

        stack_select = create_stack_select(config_manager.config)

        @ui.refreshable
        async def content():
            stack_id = cast(StackId, stack_select.value)

            rows = await run.io_bound(get_usage_rows, db, stack_id)

            ui.table(
                columns=[
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
                ],
                rows=rows or [],
                row_key="id",
            )

        stack_select.on_value_change(lambda _: content.refresh())

        async def sync_usage() -> None:
            if config_manager.config is None:
                button_sync.disable()
            else:
                for stack in config_manager.config.stacks:
                    for source in stack.sources:
                        service = get_json_placeholder_service(
                            stack_id=stack.id, source_id=source.id
                        )

                        button_sync.disable()

                        try:
                            _ = await run.io_bound(service.fetch_and_store)
                            await content.refresh()
                            message = f"Synced rows for stack {stack.name} and source {source.name}"
                            ui.notify(message)

                        except Exception as ex:
                            logger.error(
                                f"Sync failed for stack {stack.name}, source {source.name} with {ex}"
                            )
                            ui.notify(
                                f"Sync failed for stack {stack.name}, source {source.name}",
                                type="negative",
                            )

                        finally:
                            button_sync.enable()

        def reload_config() -> None:
            config_manager.load()

            if config_manager.config is not None:
                refresh_stack_select(stack_select, config_manager.config)
                message = f"Configuration loaded {config_manager.path.resolve()}"
                ui.notify(message=message)
                logger.info(message)
            else:
                message = (
                    f"Configuration failed to load {config_manager.error} from file {config_manager.path.resolve()}",
                )

                ui.notify(
                    message=message,
                    type="negative",
                    timeout=0,
                    close_button=True,
                )
                logger.error(message)

        button_sync = ui.button("sync usage", on_click=sync_usage)
        ui.button(text="reload config", on_click=reload_config)
        await content()
