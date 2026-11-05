from nicegui import ui

from varne.dependencies import get_config_manager
from varne.ui.layout import create_layout


@ui.page("/settings")
def page_settings() -> None:
    layout = create_layout()
    config_manager = get_config_manager()

    with layout:

        def save() -> None:
            error = config_manager.save_text(editor.value)
            if error is None:
                error_label.set_text("")
                ui.notify("Configuration saved")
            else:
                error_label.set_text(error)

        def reset() -> None:
            editor.set_value(config_manager.path.read_text())
            error_label.set_text("")

        ui.html("<h1>Settings</h1>")

        with ui.card():
            ui.label(str(config_manager.path.resolve())).classes("text-xs")
            editor = ui.codemirror(
                config_manager.path.read_text(), language="YAML", indent="  "
            ).classes("w-full h-96")
            error_label = ui.label().style("color: var(--chart-error-ink)")
            with ui.row():
                ui.button("Save", on_click=save)
                ui.button("Reset", on_click=reset).props("flat")
