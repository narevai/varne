"""Development-only catalog of native NiceGUI elements and their source examples."""

from textwrap import dedent

from fastapi import HTTPException
from nicegui import ui

from varne.settings import get_settings
from varne.ui.layout import create_layout

# Examples are trusted source constants, never user-supplied code. Keeping source
# alongside previews makes the gallery directly useful when writing native pages.
DEMOS: dict[str, str] = {}


def example(names: str, source: str) -> None:
    for name in names.split():
        DEMOS[name] = dedent(source).strip()


example("label", 'ui.label("A native NiceGUI label")')
example(
    "link link_target",
    """
ui.link_target('example-target')
ui.link('Jump to target', '#example-target')
""",
)
example(
    "html element",
    'ui.html("<h2>Semantic HTML</h2><p>Native content inherits the theme.</p>")',
)
example(
    "markdown",
    'ui.markdown("## Markdown\\nText with **emphasis**, `code`, and a [link](https://nicegui.io).")',
)
example(
    "restructured_text",
    'ui.restructured_text("Heading\\n=======\\n\\nText with **emphasis**.")',
)
example("code", 'ui.code("from nicegui import ui\\nui.button(\\"Save\\")")')
example("icon", 'ui.icon("dashboard")')
example("avatar", 'ui.avatar("person")')
example("badge", 'ui.badge("Connected")')
example("chip", 'ui.chip("Integration", icon="extension", removable=True)')
example(
    "button",
    """
with ui.row():
    ui.button('Primary')
    ui.button('Flat').props('flat')
    ui.button('Outline').props('outline')
    ui.button('Disabled').disable()
    ui.button('Loading').props('loading')
""",
)
example(
    "button_group",
    """
with ui.button_group():
    ui.button('First')
    ui.button('Second')
""",
)
example(
    "dropdown_button menu_item",
    """
with ui.dropdown_button('Actions'):
    ui.menu_item('Example action', on_click=lambda: ui.notify('Selected'))
""",
)
example(
    "input",
    """
ui.input('Name', placeholder='Enter a name')
ui.input('Password', password=True, password_toggle_button=True)
ui.input('Disabled', value='Read only').disable()
ui.input('Required', validation={'Required': bool}).validate()
""",
)
example("textarea", 'ui.textarea("Notes", value="Native multiline input")')
example("number", 'ui.number("Quantity", value=3, min=0, max=100)')
example("input_chips", 'ui.input_chips("Tags", value=["Development", "Example"])')
example(
    "select",
    'ui.select(["Development", "Production"], value="Development", label="Environment")',
)
example("radio", 'ui.radio(["Daily", "Weekly"], value="Daily")')
example("toggle", 'ui.toggle(["Overview", "Details"], value="Overview")')
example("checkbox", 'ui.checkbox("Enable integration", value=True)')
example("switch", 'ui.switch("Send notifications", value=True)')
example("slider", "ui.slider(min=0, max=100, value=40)")
example("range", 'ui.range(min=0, max=100, value={"min":20,"max":70})')
example("rating", "ui.rating(value=3)")
example("knob", "ui.knob(value=40, min=0, max=100)")
example("date", 'ui.date(value="2026-11-05")')
example("time", 'ui.time(value="10:30")')
example("date_input", 'ui.date_input("Date", value="2026-11-05")')
example("time_input", 'ui.time_input("Time", value="10:30")')
example("color_input", 'ui.color_input("Color", value="#287b67")')
example(
    "color_picker",
    """
with ui.button('Pick a color'):
    ui.color_picker(on_pick=lambda e: ui.notify(e.color))
""",
)
example("upload", 'ui.upload(label="Choose a file", auto_upload=False)')
example("editor", 'ui.editor(value="<p>Rich text editor</p>")')
example(
    "codemirror",
    'ui.codemirror("from nicegui import ui\\nui.button(\\"Save\\")", language="Python")',
)
example(
    "json_editor",
    'ui.json_editor({"content":{"json":{"name":"Example","enabled":True}}})',
)
example(
    "table",
    """
ui.table(columns=[{'name':'name','label':'Name','field':'name'},
                  {'name':'status','label':'Status','field':'status'}],
         rows=[{'id':1,'name':'Example integration','status':'Connected'},
               {'id':2,'name':'Another integration','status':'Pending'}],
         row_key='id', pagination=5, selection='single')
""",
)
example(
    "aggrid",
    """
ui.aggrid({'columnDefs':[{'field':'name'},{'field':'status'}],
           'rowData':[{'name':'Example integration','status':'Connected'}]})
""",
)
example(
    "tree",
    'ui.tree([{"id":"root","label":"Integrations","children":[{"id":"child","label":"Example"}]}])',
)
example("pagination", "ui.pagination(1, 10, value=1, direction_links=True)")
example("linear_progress", "ui.linear_progress(0.65)")
example("circular_progress", "ui.circular_progress(0.65)")
example(
    "spinner",
    """
with ui.row():
    for kind in ['default', 'dots', 'bars', 'rings', 'clock']:
        ui.spinner(kind)
""",
)
example(
    "skeleton",
    """
ui.skeleton('QInput')
ui.skeleton('text')
ui.skeleton('QBtn')
""",
)
example("log", 'ui.log().push("Example log entry")')
example(
    "chat_message",
    """
ui.chat_message('Can I inspect the native components?', name='You', sent=True)
ui.chat_message('Yes, all examples use the native API.', name='Assistant')
""",
)
example(
    "notification",
    'ui.button("Show notification", on_click=lambda: ui.notification("Saved", close_button=True))',
)
example(
    "tooltip",
    """
with ui.button('Hover or focus'):
    ui.tooltip('Native tooltip')
""",
)
example(
    "menu",
    """
with ui.button('Open menu'):
    with ui.menu():
        ui.menu_item('Notify', on_click=lambda: ui.notify('Selected'))
        ui.separator()
        ui.menu_item('Another action')
""",
)
example(
    "context_menu",
    """
with ui.card():
    ui.label('Right-click this card')
    with ui.context_menu():
        ui.menu_item('Example action', on_click=lambda: ui.notify('Selected'))
""",
)
example(
    "dialog",
    """
with ui.dialog() as dialog, ui.card():
    ui.label('Example dialog')
    ui.input('Name')
    ui.button('Close', on_click=dialog.close)
ui.button('Open dialog', on_click=dialog.open)
""",
)
example(
    "popup",
    """
with ui.button('Open popup'):
    with ui.popup():
        ui.label('Popup content')
        ui.input('Value')
""",
)
example(
    "expansion",
    """
with ui.expansion('Expand details', icon='info'):
    ui.label('Additional information')
""",
)
example(
    "list item item_label item_section",
    """
with ui.list():
    with ui.item():
        with ui.item_section().props('avatar'):
            ui.icon('extension')
        with ui.item_section():
            ui.item_label('Example integration')
            ui.item_label('Connected').props('caption')
""",
)
example(
    "card card_section card_actions",
    """
with ui.card():
    with ui.card_section():
        ui.label('Native card')
        ui.label('Card section content')
    with ui.card_actions():
        ui.button('Save')
""",
)
example(
    "row column space",
    """
with ui.row():
    ui.label('Left')
    ui.space()
    with ui.column():
        ui.label('First')
        ui.label('Second')
""",
)
example(
    "grid",
    """
with ui.grid(columns=2):
    for text in ['One','Two','Three','Four']:
        ui.label(text)
""",
)
example("separator", 'ui.label("Before")\nui.separator()\nui.label("After")')
example(
    "scroll_area",
    """
with ui.scroll_area():
    for i in range(30):
        ui.label(f'Row {i + 1}')
""",
)
example(
    "splitter",
    """
with ui.splitter() as splitter:
    with splitter.before:
        ui.label('Before: drag the separator')
    with splitter.after:
        ui.label('After')
""",
)
example(
    "tabs tab tab_panels tab_panel",
    """
with ui.tabs() as tabs:
    first = ui.tab('Overview')
    second = ui.tab('Details')
with ui.tab_panels(tabs, value=first):
    with ui.tab_panel(first):
        ui.label('Overview content')
    with ui.tab_panel(second):
        ui.label('Details content')
""",
)
example(
    "stepper step stepper_navigation",
    """
with ui.stepper() as stepper:
    with ui.step('Connect'):
        ui.input('Integration name')
        with ui.stepper_navigation():
            ui.button('Next', on_click=stepper.next)
    with ui.step('Finish'):
        ui.label('Ready')
        with ui.stepper_navigation():
            ui.button('Back', on_click=stepper.previous)
""",
)
example(
    "timeline timeline_entry",
    """
with ui.timeline():
    ui.timeline_entry('Created integration', title='Created', subtitle='Today', icon='add')
    ui.timeline_entry('Metadata loaded', title='Synced', icon='sync')
""",
)
example(
    "carousel carousel_slide",
    """
with ui.carousel(arrows=True, navigation=True):
    with ui.carousel_slide('first'):
        ui.label('First slide')
    with ui.carousel_slide('second'):
        ui.label('Second slide')
""",
)
example(
    "slide_item",
    'ui.slide_item("Swipe this item", on_slide=lambda e: ui.notify(e.side))',
)
example(
    "fab fab_action",
    """
with ui.fab('add'):
    ui.fab_action('edit', label='Edit', on_click=lambda: ui.notify('Edit'))
    ui.fab_action('share', label='Share', on_click=lambda: ui.notify('Share'))
""",
)
example("image", "ui.image(IMAGE)")
example(
    "interactive_image",
    'ui.interactive_image(IMAGE, on_mouse=lambda e: ui.notify(f"{e.image_x}, {e.image_y}"))',
)
example("parallax", "ui.parallax(IMAGE, height=200)")
example(
    "video",
    'ui.video("https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4")',
)
example(
    "echart",
    'ui.echart({"xAxis":{"data":["Mon","Tue","Wed"]},"yAxis":{},"series":[{"type":"bar","data":[12,18,9]}]})',
)
example("mermaid", 'ui.mermaid("graph LR; Browser-->NiceGUI; NiceGUI-->Response;")')
example("leaflet", "ui.leaflet(center=(51.5,-0.09), zoom=12)")
example(
    "scene scene_view",
    """
with ui.scene() as scene:
    scene.box()
ui.scene_view(scene)
""",
)
example(
    "joystick",
    'ui.joystick(on_move=lambda e: status.set_text(f"Position: {e.x:.2f}, {e.y:.2f}"))',
)
example("xterm", 'ui.xterm().on("ready", lambda: None)')
example(
    "plotly",
    'ui.plotly({"data":[{"type":"bar","x":["Mon","Tue","Wed"],"y":[12,18,9]}]})',
)
example(
    "altair",
    """
import altair as alt
ui.altair(alt.Chart(alt.Data(values=[{'day':'Mon','value':12},{'day':'Tue','value':18}])).mark_bar().encode(x='day:N', y='value:Q'))
""",
)
example(
    "pyplot",
    """
with ui.pyplot():
    import matplotlib.pyplot as plt
    plt.plot([1,2,3], [12,18,9])
""",
)
example(
    "matplotlib",
    """
chart = ui.matplotlib()
chart.figure.subplots().plot([1,2,3], [12,18,9])
""",
)
example("highchart", 'ui.highchart({"series":[{"data":[12,18,9]}]})')
example(
    "anywidget",
    """
import anywidget
class ExampleWidget(anywidget.AnyWidget):
    _esm = "export function render({el}) {el.textContent = 'Native widget';}"
ui.anywidget(ExampleWidget())
""",
)
example("header", 'ui.label("The gallery uses the native ui.header above.")')
example(
    "footer",
    """
with ui.footer(fixed=False):
    ui.label('Native footer')
""",
)
example(
    "drawer left_drawer right_drawer",
    """
with ui.right_drawer(value=False) as drawer:
    ui.label('Native drawer')
    ui.button('Close', on_click=drawer.hide)
ui.button('Toggle drawer', on_click=drawer.toggle)
""",
)
example(
    "page_sticky",
    """
with ui.page_sticky():
    ui.button('Sticky action', on_click=lambda: ui.notify('Clicked'))
""",
)
example(
    "page_scroller",
    """
with ui.page_scroller():
    ui.button('Scroll to top')
for i in range(80):
    ui.label(f'Scroll example {i + 1}')
""",
)
example(
    "fullscreen",
    """
fullscreen = ui.fullscreen()
ui.button('Toggle fullscreen', on_click=fullscreen.toggle)
""",
)
example(
    "dark_mode",
    'ui.label("Use the native dark-mode switch above to inspect both palettes.")',
)
example(
    "colors",
    'ui.label("Quasar theme colors are supplied globally by theme.css; no per-component palette is needed.")',
)
example(
    "keyboard",
    """
ui.keyboard(on_key=lambda e: status.set_text(f'Key: {e.key}'))
ui.label('Press a key to inspect keyboard events.')
""",
)
example(
    "timer",
    """
from datetime import datetime
ui.timer(1.0, lambda: status.set_text(datetime.now().strftime('%H:%M:%S')))
""",
)
example(
    "query",
    'ui.label("ui.query selects existing DOM elements; it has no visual component of its own.")',
)
example(
    "skip_link",
    """
target = ui.label('Skip-link destination')
ui.skip_link(target=target)
ui.label('Press Tab to reveal the skip link.')
""",
)
example(
    "teleport",
    """
target = ui.element('div')
with ui.teleport(target):
    ui.label('Teleported into the target')
""",
)
example(
    "keep_alive",
    """
with ui.keep_alive():
    ui.input('Preserved input')
""",
)
example(
    "sub_pages",
    """
ui.sub_pages({'/': lambda: ui.label('Native sub-page content')}, root_path='/dev/components')
""",
)

example("uplot", "ui.uplot({'series':[{}, {'label':'Usage'}]}, [[1,2,3],[12,18,9]])")
example("line_plot", "ui.line_plot(n=1).push([1,2,3], [[12,18,9]])")

IMAGE = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="240"><rect width="640" height="240" fill="%23eeeeee"/><text x="40" y="130" font-size="28">Image preview</text></svg>'


def render_example(name: str) -> None:
    """Render a known example. Query parameters can only select registry keys."""
    status = ui.label("Interact with the example to inspect its behavior.")
    try:
        if name in {"footer", "drawer", "left_drawer", "right_drawer"}:
            with ui.context.client.content:
                exec(
                    compile(DEMOS[name], f"<gallery:{name}>", "exec"),
                    {"ui": ui, "IMAGE": IMAGE, "status": status},
                )
        else:
            exec(
                compile(DEMOS[name], f"<gallery:{name}>", "exec"),
                {"ui": ui, "IMAGE": IMAGE, "status": status},
            )
    except ImportError as error:
        ui.label(f"This optional component requires an extra dependency: {error.name}.")
    ui.code(DEMOS[name], language="python")


@ui.page("/dev/components")
def page_gallery(component: str | None = None) -> None:
    if get_settings().environment != "development":
        raise HTTPException(status_code=404)
    if component is not None and component not in DEMOS:
        raise HTTPException(status_code=404)
    with create_layout():
        ui.html("<h1>Native NiceGUI components</h1>")
        ui.label(
            "Plain ui.* elements inheriting the global CSS theme. "
            "Jump to a component below or scroll through every example."
        )
        dark = ui.dark_mode(False)
        ui.switch("Preview dark theme", on_change=lambda e: dark.set_value(e.value))
        with ui.element("nav").classes("gallery-index"):
            ui.html(f"<h2>All {len(DEMOS)} components</h2>")
            with ui.element("ul").classes("gallery-index__list"):
                for name in sorted(DEMOS):
                    ui.html(f'<li><a href="#ui-{name}">ui.{name}</a></li>')
        for name in sorted(DEMOS):
            with ui.element("section").props(f'id="ui-{name}"').classes("gallery-demo"):
                ui.html(f"<h2>ui.{name}</h2>")
                render_example(name)
        if component is not None:
            ui.run_javascript(
                f'document.getElementById("ui-{component}")?.scrollIntoView({{block: "start"}})'
            )
