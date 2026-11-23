from nicegui import ui
from nicegui.elements.select import Select

from varne.config import ConfigVarne


def create_stack_select(config: ConfigVarne | None) -> Select:
    if config is None or not config.stacks:
        return ui.select(options={}, label="stack", value=None)

    stack_options = {stack.id: stack.name for stack in config.stacks}

    return ui.select(options=stack_options, label="stack", value=config.stacks[0].id)


def refresh_stack_select(select: Select, config: ConfigVarne):
    select.options = {stack.id: stack.name for stack in config.stacks}
    select.value = config.stacks[0].id if config.stacks else None
    select.update()
