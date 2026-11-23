from nicegui import ui

from varne.dependencies import get_config_manager
from varne.ui.components.config_form import (
    Data,
    config_form,
    form_to_yaml,
    yaml_to_form,
)
from varne.ui.layout import create_layout

YAML_TAB = "YAML"
FORM_TAB = "Form"


@ui.page("/settings")
def page_settings() -> None:
    layout = create_layout()
    config_manager = get_config_manager()

    with layout:

        def save_text(text: str) -> None:
            error = config_manager.save_text(text)
            if error is None:
                error_label.set_text("")
                ui.notify("Configuration saved")
            else:
                error_label.set_text(error)

        def save_yaml() -> None:
            save_text(editor.value)

        def save_form() -> None:
            text = form_to_yaml(form_data)
            editor.set_value(text)
            save_text(text)
            if not error_label.text:
                # what was saved is now stored: its ids are locked
                form_data.clear()
                form_data.update(yaml_to_form(text))
                form.refresh()

        def reset() -> None:
            editor.set_value(config_manager.path.read_text())
            error_label.set_text("")

        def show_form() -> None:
            """Fill the form with what the YAML says now."""
            try:
                loaded = yaml_to_form(editor.value)
            except ValueError as exc:
                error_label.set_text(str(exc))
                tabs.set_value(yaml_tab)
                return

            error_label.set_text("")
            form_shown.append(True)
            form_data.clear()
            form_data.update(loaded)
            form.refresh()

        def on_tab(value: object) -> None:
            if value is form_tab:
                show_form()
            elif form_shown:
                # what was done in the form is what the file will say
                editor.set_value(form_to_yaml(form_data))

        ui.html("<h1>Settings</h1>")

        try:
            form_data: Data = yaml_to_form(config_manager.path.read_text())
        except ValueError:
            form_data = {}
        form_shown: list[bool] = []

        with ui.tabs() as tabs:
            yaml_tab = ui.tab(YAML_TAB)
            form_tab = ui.tab(FORM_TAB)

        with ui.tab_panels(tabs, value=yaml_tab).classes("w-full"):
            with ui.tab_panel(yaml_tab):
                with ui.card():
                    ui.label(str(config_manager.path.resolve())).classes("text-xs")
                    editor = ui.codemirror(
                        config_manager.path.read_text(), language="YAML", indent="  "
                    ).classes("w-full h-96")
                    with ui.row():
                        ui.button("Save", on_click=save_yaml)
                        ui.button("Reset", on_click=reset).props("flat")

            with ui.tab_panel(form_tab):
                ui.label(
                    "Saving from the form rewrites the file: comments in it are lost."
                ).classes("text-sm opacity-70")

                @ui.refreshable
                def form() -> None:
                    config_form(form_data, save_form)

                form()

        error_label = ui.label().style("color: var(--chart-error-ink)")
        tabs.on_value_change(lambda e: on_tab(e.value))
