from typing import cast

import pandas as pd
from loguru import logger
from nicegui import run, ui
from nicegui.elements.select import Select

from varne.analytics.usage import get_source_meta
from varne.config import ConfigVarne, StackId
from varne.db.types import DatabaseBackend
from varne.dependencies import get_config_manager, get_db, get_service
from varne.ui.layout import create_layout


def get_source_meta_rows(db: DatabaseBackend, stack_id: StackId) -> pd.DataFrame:
    df_result = get_source_meta(db, stack_id).to_pandas()
    return df_result


def create_stack_select(config: ConfigVarne | None) -> Select:
    if config is None or not config.stacks:
        return ui.select(options={}, label="stack", value=None)

    stack_options = {stack.id: stack.name for stack in config.stacks}

    return ui.select(
        options=stack_options, label="stack", value=config.stacks[0].id
    ).classes("w-64")


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

        async def sync_usage() -> None:
            if config_manager.config is None:
                button_sync.disable()
            else:
                for stack in config_manager.config.stacks:
                    for source in stack.sources:
                        service = get_service(stack_id=stack.id, source=source)

                        button_sync.disable()

                        try:
                            _ = await run.io_bound(service.fetch_source_meta)
                            await content.refresh()

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
                message = "Synced rows"
                ui.notify(message)

        @ui.refreshable
        async def content():
            stack_id = cast(StackId, stack_select.value)

            df_rows = await run.io_bound(get_source_meta_rows, db, stack_id)

            if df_rows is None:
              df_rows = pd.DataFrame(columns=["source_id", "source_type", "source_name"])

            df_rows = df_rows.rename(
                columns={
                    "source_id": "ID",
                    "source_type": "Type",
                    "source_name": "Name",
                }
            )

            ui.table.from_pandas(df_rows)

        ui.label("Dashboard").classes("text-2xl font-bold")

        if config_manager.config is None or not config_manager.config.stacks:
            ui.label("No stacks found, define in Settings")

        with ui.row().classes("items-center gap-4"):
            stack_select = create_stack_select(config_manager.config)
            button_sync = ui.button("sync usage", on_click=sync_usage).classes(
                "self-end"
            )
            ui.button(text="reload config", on_click=reload_config).classes("self-end")

        stack_select.on_value_change(lambda _: content.refresh())

        await content()
