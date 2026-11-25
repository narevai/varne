from collections.abc import Callable

from nicegui import ui

from varne.config import READ_ONLY_MESSAGE
from varne.dependencies import get_config_manager
from varne.ui.components.config_form import (
    Data,
    config_form,
    form_to_yaml,
    yaml_to_form,
)

YAML_TAB = "YAML"
FORM_TAB = "Form"


def config_editor(on_saved: Callable[[], None]) -> None:
    """The configuration as a form and as text, saved to the file when it is valid."""
    config_manager = get_config_manager()

    if config_manager.read_only:
        # nothing to edit: it is shown, and the text says why it cannot be changed
        ui.label(READ_ONLY_MESSAGE).classes("text-sm opacity-70")
        ui.code(config_manager.path.read_text(), language="yaml").classes("w-full")
        return

    def fail(message: str) -> None:
        ui.notify(message, type="negative", close_button=True, multi_line=True)

    def save_text(text: str) -> bool:
        error = config_manager.save_text(text)
        if error is not None:
            fail(error)
            return False

        ui.notify("Configuration saved", type="positive")
        on_saved()
        return True

    def save_yaml() -> None:
        save_text(editor.value)

    def save_form() -> None:
        text = form_to_yaml(form_data)
        editor.set_value(text)
        if save_text(text):
            # what was saved is now stored: its ids are locked
            form_data.clear()
            form_data.update(yaml_to_form(text))
            form.refresh()

    def reset() -> None:
        editor.set_value(config_manager.path.read_text())

    def show_form() -> None:
        """Fill the form with what the YAML says now."""
        try:
            loaded = yaml_to_form(editor.value)
        except ValueError as exc:
            fail(str(exc))
            tabs.set_value(yaml_tab)
            return

        form_data.clear()
        form_data.update(loaded)
        form.refresh()

    def form_changed() -> bool:
        """Whether the form says something other than the YAML does."""
        try:
            return form_to_yaml(form_data) != form_to_yaml(yaml_to_form(editor.value))
        except ValueError:
            return False

    def on_tab(value: object) -> None:
        if value is form_tab:
            show_form()
        elif form_changed():
            # what was done in the form is what the file will say, and the
            # comments of the text stay while the form changed nothing
            editor.set_value(form_to_yaml(form_data))

    try:
        form_data: Data = yaml_to_form(config_manager.path.read_text())
        form_fits = True
    except ValueError:
        form_data = {}
        form_fits = False

    with ui.tabs() as tabs:
        form_tab = ui.tab(FORM_TAB)
        yaml_tab = ui.tab(YAML_TAB)

    # a file the form cannot read is opened as text, so that it is not saved over
    with ui.tab_panels(tabs, value=form_tab if form_fits else yaml_tab).classes(
        "w-full"
    ):
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

            @ui.refreshable
            def form() -> None:
                config_form(form_data, save_form)

            form()

    tabs.on_value_change(lambda e: on_tab(e.value))
