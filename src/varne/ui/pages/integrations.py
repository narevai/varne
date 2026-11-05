from functools import partial

from loguru import logger
from nicegui import run, ui

from varne.analytics.meta import has_source_meta
from varne.config import ConfigStack, ConfigVercel
from varne.dependencies import get_config_manager, get_db, get_service
from varne.ui.layout import create_layout


@ui.page("/integrations")
async def page_integrations() -> None:
    layout = create_layout()
    db = get_db()
    config_manager = get_config_manager()

    with layout:

        async def sync_source(stack: ConfigStack, source: ConfigVercel) -> None:
            service = get_service(stack_id=stack.id, source=source)
            try:
                await run.io_bound(service.fetch_source_meta)
            except Exception as ex:
                message = f"Sync failed for {stack.name} / {source.name}: {ex}"
                logger.error(message)
                ui.notify(message, type="negative")
                return
            vercel_integrations.refresh()

        @ui.refreshable
        async def vercel_integrations() -> None:
            config = config_manager.config
            sources = [
                (stack, source)
                for stack in (config.stacks if config else [])
                for source in stack.sources
                if isinstance(source, ConfigVercel)
            ]

            if not sources:
                ui.label("No Vercel integration found in config")
                return

            with ui.row():
                for stack, source in sources:
                    synced = await run.io_bound(
                        has_source_meta, db, stack.id, source.id
                    )
                    color = "--chart-success" if synced else "--chart-error"

                    with ui.card().classes("!w-60 !p-3 !gap-1"):
                        with ui.row().classes("items-center w-full no-wrap"):
                            ui.icon("circle", size="xs").style(f"color: var({color})")
                            ui.label(source.name).classes("font-medium")
                            ui.space()
                            if not synced:
                                ui.button(
                                    "Sync", on_click=partial(sync_source, stack, source)
                                ).props("dense size=sm").classes("!min-h-0 !py-1")
                        ui.label(f"Vercel · {stack.name}").classes("text-xs")

        ui.html("<h1>Integrations</h1>")
        await vercel_integrations()
