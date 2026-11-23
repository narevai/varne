import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, cast

import yaml
from nicegui import ui

from varne.config import DEFAULT_LOOKBACK_DAYS, SourceType
from varne.ui.components.confirm import confirm

type Data = dict[str, object]
type Kind = Literal["text", "number", "list", "secret"]


@dataclass(frozen=True)
class FormField:
    key: str
    label: str
    kind: Kind = "text"
    # A secret is either written in the file or read from an environment variable.
    env_key: str | None = None
    hint: str = ""


LOOKBACK = FormField(
    "lookback_days",
    "Lookback days",
    "number",
    hint=f"how much history to pull, {DEFAULT_LOOKBACK_DAYS} by default",
)
TOKEN = FormField("api_token", "API token", "secret", env_key="api_token_env")

SOURCE_FIELDS: dict[SourceType, list[FormField]] = {
    SourceType.ANTHROPIC: [TOKEN, LOOKBACK],
    SourceType.OPENAI: [TOKEN, LOOKBACK],
    SourceType.UMAMI: [
        TOKEN,
        FormField("website_ids", "Website ids", "list", hint="separate with commas"),
        LOOKBACK,
    ],
    SourceType.VERCEL: [
        TOKEN,
        FormField("team_id", "Team id"),
        FormField(
            "project_ids",
            "Project ids",
            "list",
            hint="separate with commas, empty for all",
        ),
        LOOKBACK,
    ],
    SourceType.DOCKER: [LOOKBACK],
}

# What a Docker machine costs: a rented hourly rate, or hardware plus power.
HOURLY_COST = [FormField("hourly_cost", "Cost per hour (USD)", "number")]
HARDWARE_COST = [
    FormField("machine_cost", "Price of the machine (USD)", "number"),
    FormField(
        "amortization_years", "Amortization (years)", "number", hint="6 by default"
    ),
    FormField(
        "power_draw_watts",
        "Power draw (W)",
        "number",
        hint="give it with the electricity price",
    ),
    FormField("electricity_price_per_kwh", "Electricity (USD per kWh)", "number"),
]
BESZEL = [
    FormField("url", "Beszel URL", hint="e.g. http://beszel:8090"),
    FormField("email", "Beszel e-mail"),
    FormField("password", "Beszel password", "secret", env_key="password_env"),
]


VALUE = "Value"
ENVIRONMENT = "Environment variable"
RENTED = "Rented, per hour"
OWNED = "Own hardware"

ICONS: dict[SourceType, str] = {
    SourceType.ANTHROPIC: "psychology",
    SourceType.DOCKER: "dns",
    SourceType.OPENAI: "auto_awesome",
    SourceType.UMAMI: "insights",
    SourceType.VERCEL: "change_history",
}

# Logos of the sources that have one; the rest get an icon. Drawn in black alone.
LOGOS: dict[SourceType, str] = {
    SourceType.ANTHROPIC: "anthropic.svg",
    SourceType.DOCKER: "docker.svg",
    SourceType.OPENAI: "openai.svg",
    SourceType.UMAMI: "umami.svg",
    SourceType.VERCEL: "vercel.svg",
}
MONO = {SourceType.ANTHROPIC, SourceType.OPENAI, SourceType.UMAMI, SourceType.VERCEL}

GRID = "grid grid-cols-1 md:grid-cols-2 gap-4 w-full"
FULL = "md:col-span-2"
INPUT = "outlined dense"


def new_source(source_type: SourceType) -> Data:
    return {"id": "", "name": "", "type": source_type.value, "_new": True}


def new_stack() -> Data:
    return {"id": "", "name": "", "sources": [], "_new": True}


def prune(value: object) -> object:
    """Drop what the form left empty, so the file holds only what was filled in."""
    if isinstance(value, dict):
        pruned = {
            key: prune(item)
            for key, item in cast(Data, value).items()
            if not key.startswith("_")
        }
        return {key: item for key, item in pruned.items() if not is_empty(item)}

    if isinstance(value, list):
        return [prune(item) for item in cast(list[object], value)]

    if isinstance(value, float) and value.is_integer():
        return int(value)

    return value


def is_empty(value: object) -> bool:
    return value is None or value == "" or value == [] or value == {}


def form_to_yaml(data: Data) -> str:
    """The text of the file for what the form holds."""
    stacks = cast(list[Data], data.get("stacks", []))
    pruned = {"stacks": [prune(stack) for stack in stacks]}

    return yaml.safe_dump(pruned, sort_keys=False, allow_unicode=True)


def yaml_to_form(text: str) -> Data:
    """What the form shows for the text of a file; raises `ValueError` if it is not one."""
    try:
        raw = cast(object, yaml.safe_load(text))
    except yaml.YAMLError as exc:
        raise ValueError(str(exc)) from exc

    if raw is None:
        return {"stacks": []}
    if not isinstance(raw, dict) or not isinstance(
        cast(Data, raw).get("stacks", []), list
    ):
        raise ValueError("The file must hold a list of stacks")

    return cast(Data, raw)


def called(item: Data) -> str:
    """How an item is named in a question: by its name, else its id."""
    return f"“{item.get('name') or item.get('id') or 'without a name'}”"


def title(fallback: str) -> Callable[[object], str]:
    return lambda name: str(name) if name else fallback


def slug(text: str) -> str:
    return "_".join(re.findall(r"[a-z0-9]+", text.lower()))


def secret_input(data: Data, field: FormField) -> None:
    assert field.env_key is not None
    env_key = field.env_key
    from_env = bool(data.get(env_key))

    @ui.refreshable
    def holder() -> None:
        key = env_key if from_env else field.key
        label = (
            f"{field.label}: name of the environment variable"
            if from_env
            else field.label
        )
        data.setdefault(key, "")
        ui.input(
            label, password=not from_env, password_toggle_button=not from_env
        ).props(INPUT).bind_value(data, key).classes("w-full")

    def switch(value: str) -> None:
        nonlocal from_env
        from_env = value == ENVIRONMENT
        # exactly one of them is in the file
        data[field.key if from_env else env_key] = ""
        holder.refresh()

    with ui.column().classes(f"gap-2 {FULL}"):
        ui.toggle(
            [VALUE, ENVIRONMENT],
            value=ENVIRONMENT if from_env else VALUE,
            on_change=lambda e: switch(cast(str, e.value)),
        ).props("dense no-caps").classes("self-start")
        holder()


def field_input(data: Data, field: FormField) -> None:
    if field.kind == "secret":
        secret_input(data, field)
        return

    if field.kind == "list":
        items = cast(list[str], data.get(field.key) or [])

        def store(text: str, key: str = field.key) -> None:
            data[key] = [part.strip() for part in text.split(",") if part.strip()]

        ui.input(
            field.label, value=", ".join(items), on_change=lambda e: store(e.value)
        ).props(INPUT).props(f'hint="{field.hint}"').classes("w-full")
        return

    data.setdefault(field.key, None if field.kind == "number" else "")
    element = (
        ui.number(field.label, format="%g")
        if field.kind == "number"
        else ui.input(field.label)
    )
    element.props(INPUT).bind_value(data, field.key).classes("w-full")
    if field.hint:
        element.props(f'hint="{field.hint}"')


def section(data: Data, fields: list[FormField]) -> None:
    for field in fields:
        field_input(data, field)


def identity(data: Data) -> None:
    """Name and id. The id of a new item follows its name, and cannot change once saved."""
    data.setdefault("name", "")
    data.setdefault("id", "")
    is_new = bool(data.get("_new"))
    previous = slug(cast(str, data["name"]))

    def follow(name: str) -> None:
        nonlocal previous
        if is_new and data["id"] in ("", previous):
            data["id"] = slug(name)
        previous = slug(name)

    ui.input("Name", on_change=lambda e: follow(e.value or "")).props(INPUT).bind_value(
        data, "name"
    ).classes("w-full")

    hint = (
        "Stored with the data, it cannot be changed after saving"
        if is_new
        else "Stored with the data, it cannot be changed"
    )
    id_input = ui.input("Id").props(INPUT).props(f'hint="{hint}"')
    id_input.bind_value(data, "id").classes("w-full")
    if not is_new:
        id_input.props("readonly")


def docker_form(source: Data) -> None:
    cost = cast(Data, source.setdefault("cost", {}))
    usage = cast(Data, source.setdefault("usage", {"type": "beszel"}))
    rented = cost.get("hourly_cost") is not None

    ui.label("Cost of the machine").classes(f"text-sm opacity-70 {FULL}")

    @ui.refreshable
    def fields() -> None:
        section(cost, HOURLY_COST if rented else HARDWARE_COST)

    def switch(value: str) -> None:
        nonlocal rented
        rented = value == RENTED
        # hourly rate and hardware exclude each other
        for field in HARDWARE_COST if rented else HOURLY_COST:
            cost[field.key] = None
        fields.refresh()

    ui.toggle(
        [RENTED, OWNED],
        value=RENTED if rented else OWNED,
        on_change=lambda e: switch(cast(str, e.value)),
    ).props("dense no-caps").classes(f"self-start justify-self-start {FULL}")
    with ui.element("div").classes(f"{GRID} {FULL}"):
        fields()

    ui.label("Usage from Beszel").classes(f"text-sm opacity-70 {FULL}")
    section(usage, BESZEL)


def source_logo(source_type: SourceType) -> None:
    logo = LOGOS.get(source_type)
    if logo is None:
        ui.icon(ICONS[source_type], size="28px").classes("opacity-70")
        return

    image = (
        ui.image(f"/ui-assets/sources/{logo}")
        .props("fit=contain")
        .classes("w-7 h-7 flex-none")
    )
    if source_type in MONO:
        image.classes("logo-mono")


def source_form(source: Data, on_remove: Callable[[], None]) -> None:
    try:
        source_type = SourceType(source.get("type"))
    except ValueError:
        with ui.card().classes("w-full"):
            ui.label(f"Unknown source type {source.get('type')!r}, edit it in YAML")
            ui.button(icon="delete", on_click=on_remove).props("flat dense")
        return

    with ui.expansion().classes("w-full border rounded") as panel:
        with panel.add_slot("header"):
            with ui.row().classes("items-center no-wrap w-full"):
                source_logo(source_type)
                with ui.column().classes("gap-0"):
                    ui.label().bind_text_from(source, "name", title("New source"))
                    ui.label(source_type.value).classes("text-xs opacity-60")
                ui.space()
                ui.button(icon="delete", on_click=on_remove).props(
                    "flat round dense color=negative"
                ).on("click.stop")

        with ui.element("div").classes(f"{GRID} p-4"):
            identity(source)
            if source_type is SourceType.DOCKER:
                docker_form(source)
            section(source, SOURCE_FIELDS[source_type])


def config_form(data: Data, on_save: Callable[[], None]) -> None:
    """A form for the stacks and sources of the configuration, edited in `data`."""
    stacks = cast(list[Data], data.setdefault("stacks", []))

    @ui.refreshable
    def form() -> None:
        if not stacks:
            ui.label(
                "No stacks yet. A stack groups the sources of one product."
            ).classes("opacity-70")

        for stack in stacks:
            stack_form(stack)

        ui.button("Add stack", icon="add", on_click=add_stack).props("outline no-caps")

    def add_stack() -> None:
        stacks.append(new_stack())
        form.refresh()

    def stack_form(stack: Data) -> None:
        sources = cast(list[Data], stack.setdefault("sources", []))

        with ui.card().classes("w-full gap-4"):
            with ui.row().classes("w-full items-center no-wrap"):
                ui.icon("layers").classes("opacity-70")
                ui.label().classes("text-lg").bind_text_from(
                    stack, "name", title("New stack")
                )
                ui.space()
                ui.button(
                    icon="delete",
                    on_click=lambda: confirm(
                        f"Delete the stack {called(stack)} with all its sources?",
                        lambda: remove(stacks, stack),
                    ),
                ).props("flat round dense color=negative")

            with ui.element("div").classes(GRID):
                identity(stack)

            ui.label("Sources").classes("text-sm opacity-70")
            if not sources:
                ui.label("No sources yet.").classes("text-sm opacity-60")
            for source in sources:
                source_form(
                    source,
                    lambda source=source: confirm(
                        f"Delete the source {called(source)}?",
                        lambda: remove(sources, source),
                    ),
                )

            with ui.button("Add source", icon="add").props("outline no-caps"):
                with ui.menu():
                    for source_type in SourceType:
                        ui.menu_item(source_type.value, adder(sources, source_type))

    def adder(sources: list[Data], source_type: SourceType) -> Callable[[], None]:
        def add() -> None:
            sources.append(new_source(source_type))
            form.refresh()

        return add

    def remove(items: list[Data], item: Data) -> None:
        items.remove(item)
        form.refresh()

    with ui.row().classes("w-full items-center"):
        ui.label("Stacks and their sources").classes("text-lg")
        ui.space()
        ui.button("Save", icon="save", on_click=on_save)
    form()
