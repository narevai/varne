from nicegui import ui


def nav_item(label: str, icon: str, target: str):
    with ui.item(on_click=lambda: ui.navigate.to(target)) as item:
        if ui.context.client.page.path == target:
            item.props("aria-current=page")
        with ui.item_section().props("side"):
            ui.icon(icon)
        with ui.item_section():
            ui.label(label)
