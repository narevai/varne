from nicegui import app, ui

from varne.settings import get_settings

settings = get_settings()

app.add_static_files("/ui-assets", settings.static_path)
ui.add_css((settings.static_path / "theme.css").read_text(), shared=True)

# Behaviour that CSS cannot give, in files of their own next to the theme.
for script in ("bar-labels.js", "chart-tooltips.js"):
    ui.add_head_html(f'<script src="/ui-assets/{script}" defer></script>', shared=True)
