from typing import cast

import pandas as pd
from loguru import logger
from nicegui import run, ui
from nicegui.events import GenericEventArguments

from varne.analytics.billing import get_billing_per_day, get_source_billing
from varne.analytics.cost_per_usage import get_source_cost_per_usage
from varne.analytics.meta import has_source_meta
from varne.analytics.usage import get_source_usage
from varne.config import ConfigSource, ConfigStack, SourceId, SourceType, StackId
from varne.db.lock import serialized
from varne.db.sources import delete_source_data, stored_source_ids
from varne.db.types import DatabaseBackend
from varne.dependencies import get_config_manager, get_db, get_service
from varne.ui.components.application_costs import application_costs
from varne.ui.components.bar_chart import bar_chart
from varne.ui.components.confirm import confirm
from varne.ui.components.empty_state import no_sources, no_stacks
from varne.ui.components.page_header import page_header
from varne.ui.components.stack_select import create_stack_select
from varne.ui.layout import create_layout

CHART_ROWS = 1000

# A source that is stored but no longer configured is grey and can only be removed.
SOURCE_ROW = """
<q-tr :props="props" :class="props.row.orphan ? 'opacity-50' : ''">
    <q-td v-for="col in props.cols" :key="col.name" :props="props">
        <template v-if="col.name === 'action'">
            <q-btn v-if="props.row.orphan" flat dense color="negative" icon="delete"
                   @click="() => $parent.$emit('remove', props.row.id)" />
            <q-btn v-else flat label="Pull"
                   @click="() => $parent.$emit('pull', props.row.id)" />
        </template>
        <template v-else>{{ col.value }}</template>
    </q-td>
</q-tr>
"""


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
def get_billing_per_day_rows(
    db: DatabaseBackend, stack_id: StackId, source_ids: list[SourceId]
) -> pd.DataFrame:
    df_result = get_billing_per_day(db, stack_id, source_ids).to_pandas()
    return df_result


@serialized
def get_cost_per_usage_rows(
    db: DatabaseBackend, stack_id: StackId, source_id: SourceId
) -> pd.DataFrame:
    df_result = get_source_cost_per_usage(db, stack_id, source_id).to_pandas()
    return df_result


@ui.page("/")
async def page_dashboard() -> None:
    config_manager = get_config_manager()
    # the file may have been edited outside of the app since the page was last opened
    _ = config_manager.load()
    layout = create_layout()
    db = get_db()

    with layout:

        def selected_stack_id() -> StackId | None:
            return cast(StackId | None, stack_select.value)

        def selected_stack_sources() -> list[ConfigSource]:
            stack = selected_stack()
            return list(stack.sources) if stack is not None else []

        def selected_stack() -> ConfigStack | None:
            config = config_manager.config
            if config is None:
                return None
            stack_id = selected_stack_id()
            return next((x for x in config.stacks if x.id == stack_id), None)

        async def pull(sources: list[ConfigSource]) -> None:
            """Pull what the sources hold: their metadata and their data."""
            stack = selected_stack()
            if stack is None or not sources:
                ui.notify("No sources in this stack, define them in Settings")
                return

            button_pull.disable()
            pulled = 0
            try:
                for source in sources:
                    service = get_service(stack_id=stack.id, source=source)

                    try:
                        await run.io_bound(service.fetch_source_meta)
                        await run.io_bound(service.fetch_source_data)
                        pulled += 1
                    except Exception as ex:
                        message = f"Pull failed for {stack.name} / {source.name}: {ex}"
                        logger.error(message)
                        ui.notify(message, type="negative")
            finally:
                button_pull.enable()

            await content.refresh()
            if pulled:
                ui.notify(f"Pulled {pulled} source(s)")

        async def remove_one(e: GenericEventArguments) -> None:
            stack = selected_stack()
            if stack is None:
                return

            source_id = cast(SourceId, e.args)

            async def remove() -> None:
                await run.io_bound(delete_source_data, db, stack.id, source_id)
                ui.notify(f"Removed the data of {source_id}")
                await content.refresh()

            confirm(
                f"Delete everything stored for {source_id}? This cannot be undone.",
                remove,
            )

        async def pull_one(e: GenericEventArguments) -> None:
            stack = selected_stack()
            source = next(
                (
                    x
                    for x in (stack.sources if stack is not None else [])
                    if x.id == cast(SourceId, e.args)
                ),
                None,
            )
            if source is None:
                ui.notify(
                    "Source not found in the current configuration", type="negative"
                )
                return

            await pull([source])

        async def total_cost() -> None:
            stack = selected_stack()
            if stack is None:
                return

            # what is no longer in the configuration is not shown, whatever is stored
            source_names = {source.id: source.name for source in stack.sources}
            df_total = await run.io_bound(
                get_billing_per_day_rows, db, stack.id, list(source_names)
            )

            if df_total.empty:
                return

            df_total["source"] = [
                source_names[source_id]
                for source_id in cast(list[str], df_total["source_id"].tolist())
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
            stack = selected_stack()
            if stack is None:
                return

            if not stack.sources:
                no_sources()
                return

            configured = {source.id for source in stack.sources}
            stored = await run.io_bound(stored_source_ids, db, stack.id)
            rows = [
                {
                    "id": source.id,
                    "name": source.name,
                    "type": source.type.title(),
                    "status": "Pulled"
                    if await run.io_bound(has_source_meta, db, stack.id, source.id)
                    else "Not pulled yet",
                    "orphan": False,
                }
                for source in stack.sources
            ] + [
                {
                    "id": source_id,
                    "name": source_id,
                    "type": "",
                    "status": "Not in the configuration",
                    "orphan": True,
                }
                for source_id in stored
                if source_id not in configured
            ]
            table = ui.table(
                columns=[
                    {"name": "name", "label": "Name", "field": "name", "align": "left"},
                    {"name": "type", "label": "Type", "field": "type", "align": "left"},
                    {
                        "name": "status",
                        "label": "Status",
                        "field": "status",
                        "align": "left",
                    },
                    {"name": "action", "label": "", "field": "action"},
                ],
                rows=rows,
                row_key="id",
                title="Sources",
            ).classes("w-full")
            table.add_slot("body", SOURCE_ROW)
            table.on("pull", lambda e: pull_one(e))
            table.on("remove", lambda e: remove_one(e))
            await total_cost()
            await source_detail()

        page_header(
            "Dashboard", "What your sources cost, and when you last pulled them."
        )

        if config_manager.config is None or not config_manager.config.stacks:
            no_stacks()
            return

        with ui.row():
            stack_select = create_stack_select(config_manager.config)
            button_pull = ui.button(
                "Pull all",
                icon="sync",
                on_click=lambda: pull(selected_stack_sources()),
            )

        stack_select.on_value_change(lambda _: content.refresh())

        await content()
