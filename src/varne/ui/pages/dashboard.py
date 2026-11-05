from typing import cast

import pandas as pd
from loguru import logger
from nicegui import run, ui
from nicegui.elements.select import Select
from nicegui.events import GenericEventArguments

from varne.analytics.billing import get_source_billing
from varne.analytics.cost_per_usage import get_source_cost_per_usage
from varne.analytics.meta import get_source_meta
from varne.analytics.usage import get_source_usage
from varne.config import ConfigVarne, SourceId, StackId
from varne.db.types import DatabaseBackend
from varne.dependencies import get_config_manager, get_db, get_service
from varne.ui.components.bar_chart import bar_chart
from varne.ui.layout import create_layout

CHART_ROWS = 1000


def get_source_meta_rows(db: DatabaseBackend, stack_id: StackId) -> pd.DataFrame:
    df_result = get_source_meta(db, stack_id).to_pandas()
    return df_result


def get_billing_rows(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> pd.DataFrame:
    df_result = get_source_billing(
        db, stack_id, source_id, page_size=CHART_ROWS
    ).to_pandas()
    return df_result


def get_usage_rows(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> pd.DataFrame:
    df_result = get_source_usage(
        db, stack_id, source_id, page_size=CHART_ROWS
    ).to_pandas()
    return df_result


def get_cost_per_usage_rows(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> pd.DataFrame:
    df_result = get_source_cost_per_usage(db, stack_id, source_id).to_pandas()
    return df_result


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

        async def sync_meta() -> None:
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

        async def pull_billing(e: GenericEventArguments) -> None:
            if config_manager.config is None:
                return
            stack_id = cast(StackId, stack_select.value)
            stack = next(x for x in config_manager.config.stacks if x.id == stack_id)

            source_id = cast(SourceId, e.args)
            source = next(x for x in stack.sources if x.id == source_id)

            service = get_service(stack_id=stack.id, source=source)

            try:
                _ = await run.io_bound(service.fetch_source_data)

            except Exception as ex:
                message = f"Pull failed for stack {stack.name}, source {source.name} with {ex}"
                logger.error(message)
                ui.notify(message, type="negative")

        @ui.refreshable
        async def source_detail() -> None:
            stack_id = cast(StackId, stack_select.value)
            source_id = "vercel1"

            with ui.card():
                with ui.row():
                    ui.label(str(source_id))

                df_billing = await run.io_bound(
                    get_billing_rows, db, stack_id, source_id
                )

                if df_billing.empty:
                    ui.label("No billing data available")
                    return

                currencies = ", ".join(
                    cast(list[str], df_billing["billing_currency"].unique().tolist())
                )
                bar_chart(
                    f"Billing ({currencies})",
                    df_billing,
                    x="charge_period_start",
                    y="billed_cost",
                    series="service_name",
                    value_format=".2~r",
                )

                df_usage = await run.io_bound(get_usage_rows, db, stack_id, source_id)

                if df_usage.empty:
                    ui.label("No usage data available")
                    return

                units = ", ".join(
                    cast(list[str], df_usage["usage_name"].unique().tolist())
                )
                bar_chart(
                    f"Usage ({units})",
                    df_usage,
                    x="event_time",
                    y="usage",
                    series="usage_name",
                )

                df_cost = await run.io_bound(
                    get_cost_per_usage_rows, db, stack_id, source_id
                )

                if df_cost.empty:
                    return

                bar_chart(
                    f"Cost per visitor ({currencies})",
                    df_cost,
                    x="day",
                    y="cost_per_usage",
                    series="series",
                    value_format=".2~r",
                )

        @ui.refreshable
        async def content():
            stack_id = cast(StackId, stack_select.value)

            df_rows = await run.io_bound(get_source_meta_rows, db, stack_id)

            if df_rows.empty:
                df_rows = pd.DataFrame(
                    columns=["source_id", "source_type", "source_name"]
                )

            df_rows = df_rows.rename(
                columns={
                    "source_id": "ID",
                    "source_type": "Type",
                    "source_name": "Name",
                }
            )

            df_rows["action"] = None

            table = ui.table.from_pandas(df_rows, title="Synced metadata")
            with table.add_slot("body-cell-action"):
                with table.cell("action"):
                    ui.button("Pull billing").props("flat").on(
                        "click",
                        js_handler="() => emit(props.row.ID)",
                        handler=lambda e: pull_billing(e),
                    )
            await source_detail()

        ui.html("<h1>Dashboard</h1>")

        if config_manager.config is None or not config_manager.config.stacks:
            ui.label("No stacks found, define in Settings")

        with ui.row():
            stack_select = create_stack_select(config_manager.config)
            button_sync = ui.button("sync metadata", on_click=sync_meta)
            ui.button(text="reload config", on_click=reload_config)

        stack_select.on_value_change(lambda _: content.refresh())

        await content()
