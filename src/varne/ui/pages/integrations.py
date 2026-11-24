from datetime import UTC, datetime
from typing import cast

from loguru import logger
from nicegui import run, ui
from nicegui.events import GenericEventArguments

from varne.config import (
    ConfigSource,
    ConfigStack,
    SourceId,
    StackId,
    offered_sources,
)
from varne.db.sources import delete_source_data, last_synced, stored_source_ids
from varne.dependencies import get_config_manager, get_db, get_service
from varne.ui.components.config_editor import config_editor
from varne.ui.components.confirm import confirm
from varne.ui.components.stack_select import create_stack_select
from varne.ui.layout import create_layout

# A source that is stored but no longer configured is grey and can only be removed.
SOURCE_ROW = """
<q-tr :props="props" :class="props.row.orphan ? 'opacity-50' : ''">
    <q-td v-for="col in props.cols" :key="col.name" :props="props">
        <template v-if="col.name === 'action'">
            <q-btn v-if="props.row.orphan" flat dense color="negative" icon="delete"
                   @click="() => $parent.$emit('remove', props.row.id)" />
            <q-btn v-else flat label="Sync" icon="sync"
                   @click="() => $parent.$emit('sync', props.row.id)" />
        </template>
        <template v-else>{{ col.value }}</template>
    </q-td>
</q-tr>
"""


def when(at: datetime | None) -> str:
    if at is None:
        return "Never"

    at = at.replace(tzinfo=UTC) if at.tzinfo is None else at.astimezone(UTC)
    return at.strftime("%b %d, %Y %H:%M UTC")


@ui.page("/integrations")
async def page_integrations() -> None:
    config_manager = get_config_manager()
    # the file may have been edited outside of the app since the page was last opened
    _ = config_manager.load()
    layout = create_layout("Integrations")
    db = get_db()

    with layout:

        def selected_stack() -> ConfigStack | None:
            config = config_manager.config
            if config is None:
                return None
            return next(
                (x for x in config.stacks if x.id == cast(StackId, stack_select.value)),
                None,
            )

        async def sync(sources: list[ConfigSource]) -> None:
            """Pull what the sources hold: their metadata and their data."""
            stack = selected_stack()
            if stack is None or not sources:
                ui.notify("No sources in this stack, define them in Settings")
                return

            button_sync_all.disable()
            synced = 0
            try:
                for source in sources:
                    service = get_service(stack_id=stack.id, source=source)

                    try:
                        await run.io_bound(service.fetch_source_meta)
                        await run.io_bound(service.fetch_source_data)
                        synced += 1
                    except Exception as ex:
                        message = f"Sync failed for {stack.name} / {source.name}: {ex}"
                        logger.error(message)
                        ui.notify(message, type="negative")
            finally:
                button_sync_all.enable()

            await content.refresh()
            if synced:
                ui.notify(f"Synced {synced} source(s)")

        async def sync_one(e: GenericEventArguments) -> None:
            stack = selected_stack()
            source = next(
                (
                    x
                    for x in (offered_sources(stack) if stack is not None else [])
                    if x.id == cast(SourceId, e.args)
                ),
                None,
            )
            if source is None:
                ui.notify(
                    "Source not found in the current configuration", type="negative"
                )
                return

            await sync([source])

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

        @ui.refreshable
        async def content() -> None:
            stack = selected_stack()
            if stack is None:
                return

            sources = offered_sources(stack)
            if not sources:
                ui.label("This stack has no sources. Add one below.").classes(
                    "text-sm opacity-70"
                )
                return

            configured = {source.id for source in stack.sources}
            stored = await run.io_bound(stored_source_ids, db, stack.id)
            synced = await run.io_bound(last_synced, db, stack.id)
            rows = [
                {
                    "id": source.id,
                    "name": source.name,
                    "type": source.type.title(),
                    "synced": when(synced.get(source.id)),
                    "orphan": False,
                }
                for source in sources
            ] + [
                {
                    "id": source_id,
                    "name": source_id,
                    "type": "Not in the configuration",
                    "synced": when(synced.get(source_id)),
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
                        "name": "synced",
                        "label": "Last synced",
                        "field": "synced",
                        "align": "left",
                    },
                    {"name": "action", "label": "", "field": "action"},
                ],
                rows=rows,
                row_key="id",
            ).classes("w-full")
            table.add_slot("body", SOURCE_ROW)
            table.on("sync", lambda e: sync_one(e))
            table.on("remove", lambda e: remove_one(e))

        if config_manager.config is None or not config_manager.config.stacks:
            ui.label("No stacks yet. Add one below.").classes("text-sm opacity-70")
        else:
            with layout.header_tools:
                stack_select = create_stack_select(config_manager.config)
            button_sync_all = ui.button(
                "Sync all",
                icon="sync",
                on_click=lambda: sync(
                    offered_sources(stack) if (stack := selected_stack()) else []
                ),
            )

            stack_select.on_value_change(lambda _: content.refresh())

            await content()

        # saving can change the stacks and the sources, so the page starts over
        def start_over() -> None:
            ui.timer(0.6, ui.navigate.reload, once=True)

        # the editor is a section of its own, not a filter of the table above it
        with ui.column().classes("config-section"):
            ui.label("Configuration").classes("section-title")
            config_editor(on_saved=start_over)


@ui.page("/settings")
def page_settings() -> None:
    """The configuration lives with the integrations now."""
    ui.navigate.to("/integrations")
