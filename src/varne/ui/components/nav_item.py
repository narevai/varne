from nicegui import ui


def nav_item(label: str, icon: str, target: str, external: bool = False):
    with ui.item(on_click=None if external else lambda: ui.navigate.to(target)) as item:
        if external:
            item.props(f"href={target} target=_blank rel=noopener")
        elif ui.context.client.page.path == target:
            item.props("aria-current=page")
        with ui.item_section().props("side"):
            ui.icon(icon)
        with ui.item_section():
            ui.label(label)
