from typing import cast

import pandas as pd
from loguru import logger
from nicegui import run, ui
from nicegui.events import GenericEventArguments

from varne.analytics.billing import get_billing_per_day, get_source_billing
from varne.analytics.cost_per_usage import get_source_cost_per_usage
from varne.analytics.meta import get_source_meta
from varne.analytics.usage import get_source_usage
from varne.config import ConfigStack, SourceId, SourceType, StackId
from varne.db.lock import serialized
from varne.db.types import DatabaseBackend
from varne.dependencies import get_config_manager, get_db, get_service
from varne.ui.components.application_costs import application_costs
from varne.ui.components.bar_chart import bar_chart
from varne.ui.components.stack_select import (
    create_stack_select,
    refresh_stack_select,
)
from varne.ui.layout import create_layout

CHART_ROWS = 1000


@serialized
def get_source_meta_rows(db: DatabaseBackend, stack_id: StackId) -> pd.DataFrame:
    df_result = get_source_meta(db, stack_id).to_pandas()
    return df_result


@serialized
def get_billing_rows(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> pd.DataFrame:
    df_result = get_source_billing(db, stack_id, source_id).to_pandas()
    return df_result


@serialized
def get_usage_rows(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> pd.DataFrame:
    df_result = get_source_usage(
        db, stack_id, source_id, page_size=CHART_ROWS
    ).to_pandas()
    return df_result


@serialized
def get_billing_per_day_rows(db: DatabaseBackend, stack_id: StackId) -> pd.DataFrame:
    df_result = get_billing_per_day(db, stack_id).to_pandas()
    return df_result


@serialized
def get_cost_per_usage_rows(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> pd.DataFrame:
    df_result = get_source_cost_per_usage(db, stack_id, source_id).to_pandas()
    return df_result


@ui.page("/")
async def page_dashboard() -> None:
    layout = create_layout()
    db = get_db()
    config_manager = get_config_manager()

    with layout:

        def selected_stack_id() -> StackId | None:
            return cast(StackId | None, stack_select.value)

        def selected_stack() -> ConfigStack | None:
            config = config_manager.config
            if config is None:
                return None
            stack_id = selected_stack_id()
            return next((x for x in config.stacks if x.id == stack_id), None)

        async def reload_config() -> None:
            config_manager.load()

            selected_before = selected_stack_id()
            if config_manager.config is not None:
                refresh_stack_select(stack_select, config_manager.config)

            if config_manager.error is not None:
                message = f"Configuration failed to load {config_manager.error} from file {config_manager.path.resolve()}"
                ui.notify(
                    message=message,
                    type="negative",
                    timeout=0,
                    close_button=True,
                )
                logger.error(message)
            else:
                message = f"Configuration loaded {config_manager.path.resolve()}"
                ui.notify(message=message)
                logger.info(message)

            if selected_stack_id() == selected_before:
                await content.refresh()

        async def sync_meta() -> None:
            stack = selected_stack()
            if stack is None or not stack.sources:
                ui.notify("No sources in this stack, define them in Settings")
                return

            synced = 0
            button_sync.disable()
            try:
                for source in stack.sources:
                    service = get_service(stack_id=stack.id, source=source)

                    try:
                        _ = await run.io_bound(service.fetch_source_meta)
                        synced += 1
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

            await content.refresh()
            if synced:
                ui.notify(f"Synced {synced} source(s)")

        async def pull_billing(e: GenericEventArguments) -> None:
            stack = selected_stack()
            source = (
                next((x for x in stack.sources if x.id == cast(SourceId, e.args)), None)
                if stack is not None
                else None
            )
            if stack is None or source is None:
                ui.notify(
                    "Source not found in the current configuration", type="negative"
                )
                return

            service = get_service(stack_id=stack.id, source=source)

            try:
                _ = await run.io_bound(service.fetch_source_data)
            except Exception as ex:
                message = f"Pull failed for stack {stack.name}, source {source.name} with {ex}"
                logger.error(message)
                ui.notify(message, type="negative")
                return

            ui.notify(f"Pulled data for {source.name}")
            await content.refresh()

        async def total_cost() -> None:
            if config_manager.config is None:
                return

            stack_id = selected_stack_id()
            if stack_id is None:
                return

            df_total = await run.io_bound(get_billing_per_day_rows, db, stack_id)

            if df_total.empty:
                return

            source_names = {
                (stack.id, source.id): source.name
                for stack in config_manager.config.stacks
                for source in stack.sources
            }
            df_total["source"] = [
                source_names.get((stack_id, source_id), source_id)
                for stack_id, source_id in zip(
                    cast(list[str], df_total["stack_id"].tolist()),
                    cast(list[str], df_total["source_id"].tolist()),
                    strict=True,
                )
            ]

            currencies = ", ".join(
                cast(list[str], df_total["currency"].unique().tolist())
            )
            with ui.card():
                bar_chart(
                    f"Cost per day ({currencies})",
                    df_total,
                    x="day",
                    y="cost",
                    series="source",
                    value_format=".2~r",
                )

        async def source_card(
            stack_id: StackId,
            source_id: SourceId,
            source_name: str,
            source_type: SourceType,
        ) -> None:
            with ui.card():
                with ui.row():
                    ui.label(source_name)

                if source_type == SourceType.DOCKER:
                    await application_costs(db, stack_id, source_id)
                    return

                df_billing = await run.io_bound(
                    get_billing_rows, db, stack_id, source_id
                )

                currencies = ""
                if df_billing.empty:
                    ui.label("No billing data available")
                else:
                    currencies = ", ".join(
                        cast(
                            list[str], df_billing["billing_currency"].unique().tolist()
                        )
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

                if df_billing.empty:
                    return

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
        async def source_detail() -> None:
            stack = selected_stack()
            if stack is None:
                return

            for source in stack.sources:
                await source_card(stack.id, source.id, source.name, source.type)

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
            await total_cost()
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
