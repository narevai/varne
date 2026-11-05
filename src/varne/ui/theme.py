from nicegui import app, ui

from varne.settings import get_settings

settings = get_settings()

app.add_static_files("/ui-assets", settings.static_path)
ui.add_css((settings.static_path / "theme.css").read_text(), shared=True)
