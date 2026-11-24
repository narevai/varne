from decimal import Decimal
from typing import NamedTuple, cast

from nicegui import run, ui

from varne.catalog.apps import ALTERNATIVE_ICONS
from varne.catalog.comparison import (
    OTHER,
    AppComparison,
    Comparison,
    compare,
)
from varne.catalog.images import ICON_FILES
from varne.config import StackId, offered_sources
from varne.dependencies import get_config_manager, get_db
from varne.ui.components.application_costs import application_costs
from varne.ui.components.container_costs import get_container_cost_rows
from varne.ui.components.container_names import container_label
from varne.ui.components.empty_state import empty_state, no_sources, no_stacks
from varne.ui.components.stack_select import create_stack_select
from varne.ui.layout import create_layout

ROW_WITH_LOGO = """
<q-td :props="props">
    <div class="row items-center no-wrap" style="gap: 12px">
        <img v-if="props.row.icon" :src="props.row.icon"
             style="width: 28px; height: 28px; flex: none; object-fit: contain" />
        <q-icon v-else :name="props.row.symbol || 'apps'" size="28px" class="opacity-40" />
        <div>
            <div>{{ props.value }}</div>
            <div class="text-caption opacity-60" style="word-break: break-all">
                {{ props.row.containers }}
                <q-tooltip v-if="props.row.all_containers" style="white-space: pre-line">
                    {{ props.row.all_containers }}
                </q-tooltip>
            </div>
        </div>
    </div>
</q-td>
"""
DIFFERENCE_CELL = """
<q-td :props="props" :class="props.row.tone"><b>{{ props.value }}</b></q-td>
"""


def dollars(amount: Decimal | None) -> str:
    if amount is None:
        return "—"

    # a container costs fractions of a cent an hour, cents alone would show $0.00
    if 0 < abs(amount) < Decimal("0.01"):
        return f"${amount:.4f}"

    return f"${amount:,.2f}"


def percent(value: Decimal | None) -> str:
    return "n/a" if value is None else f"{value:+.0%}"


def money(amount: Decimal) -> str:
    """Dollars, with the sign in front of the dollar sign."""
    if amount < 0:
        return f"-{dollars(-amount)}"

    return dollars(amount)


def plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def tone(amount: Decimal | None) -> str:
    if amount is None:
        return ""

    return "text-positive" if amount >= 0 else "text-negative"


def number_column(name: str, label: str) -> dict[str, str]:
    return {"name": name, "label": label, "field": name, "align": "right"}


def figure(label: str, amount: Decimal) -> None:
    with ui.row().classes("w-full justify-between items-baseline"):
        ui.label(label).classes("text-sm")
        with ui.row().classes("items-baseline gap-1"):
            ui.label(dollars(amount)).classes("statement-figure")
            ui.label("/ mo").classes("text-sm opacity-60")


class Segment(NamedTuple):
    """One part of a bar: what it is worth, what it says, and what it is."""

    amount: Decimal
    kind: str
    tip: str
    # Written on it when there is room: the logo if there is one, else the text.
    text: str = ""
    logo: str = ""


def bar(segments: list[Segment], scale: Decimal, ordered: bool = False) -> None:
    """One bar, on a scale that it shares with the other.

    What is written on a segment is shown where it fits, see theme.py. On an ordered
    bar it stops at the first segment that has nothing to write or no room for it: no
    segment to its right is written on.
    """
    stopped = False
    with ui.element("div").classes("bar bar-ordered" if ordered else "bar"):
        for segment in segments:
            if segment.amount <= 0 or scale <= 0:
                continue

            if ordered and not (segment.logo or segment.text):
                stopped = True

            width = f"{float(segment.amount / scale * 100):.2f}%"
            with (
                ui.element("div")
                .classes(f"bar-seg {segment.kind}")
                .style(f"width: {width}")
            ):
                if (segment.logo or segment.text) and not stopped:
                    with ui.element("div").classes("seg-text"):
                        if segment.logo:
                            ui.element("img").props(f"src={segment.logo}").classes(
                                "seg-logo"
                            )
                        else:
                            ui.label(segment.text)
                # a mouse hovers over it, a finger taps it and the tip stays until the next tap
                ui.tooltip(segment.tip).classes("seg-tip").style(
                    "white-space: pre-line"
                )
                with (
                    ui.menu()
                    .classes("seg-menu")
                    .props("anchor='top middle' self='bottom middle'")
                ):
                    ui.label(segment.tip).classes("px-3 py-2 text-sm").style(
                        "white-space: pre-line"
                    )


def statement_rows(comparison: Comparison) -> list[dict[str, str]]:
    compared = [
        app
        for app in comparison.apps
        if app.alternative is not None and app.avoided_cost is not None
    ]
    rest = [app for app in comparison.apps if app not in compared]

    def row(app: AppComparison) -> dict[str, str]:
        difference = (app.avoided_cost or Decimal(0)) - app.self_hosted
        return {
            "app": app.app,
            "icon": f"/ui-assets/icons/{ICON_FILES[app.icon]}" if app.icon else "",
            "symbol": "apps",
            "containers": container_label(app.containers),
            "all_containers": "\n".join(app.containers)
            if len(app.containers) > 1
            else "",
            "self_hosted": dollars(app.self_hosted),
            "alternative": app.alternative or "",
            "avoided_cost": dollars(app.avoided_cost),
            "difference": money(difference),
            "tone": tone(difference),
        }

    def left_out(name: str, symbol: str, cost: Decimal, count: str) -> dict[str, str]:
        return {
            "app": name,
            "icon": "",
            "symbol": symbol,
            "containers": count,
            "all_containers": "",
            "self_hosted": dollars(cost),
            "alternative": "Not compared",
            "avoided_cost": "—",
            "difference": f"({dollars(cost)})",
            "tone": "text-negative",
        }

    rows = [row(app) for app in compared]
    if rest:
        count = sum(len(app.containers) if app.app == OTHER else 1 for app in rest)
        rows.append(
            left_out(
                plural(count, "other app"),
                "more_horiz",
                sum((app.self_hosted for app in rest), Decimal(0)),
                "",
            )
        )
    if comparison.idle > 0:
        rows.append(left_out("Idle", "hourglass_empty", comparison.idle, ""))

    return rows


def dashboard_view(comparison: Comparison, name: str) -> None:
    hosted: dict[str, Decimal] = {
        app.alternative: app.avoided_cost
        for app in comparison.apps
        if app.alternative is not None and app.avoided_cost is not None
    }
    # the logo of the subscription, or else of the first application that stands in
    # for it
    logos: dict[str, str] = {}
    for app in comparison.apps:
        icon = ALTERNATIVE_ICONS.get(app.alternative or "") or app.icon
        if app.alternative and icon and app.alternative not in logos:
            logos[app.alternative] = f"/ui-assets/icons/{ICON_FILES[icon]}"
    apps = sum(
        len(app.containers) if app.app == OTHER else 1 for app in comparison.apps
    )
    scale = max(comparison.avoided_cost, comparison.machine_cost)
    used = comparison.machine_cost - comparison.idle

    with ui.row().classes("items-center gap-3"):
        ui.label(name).classes("stack-title")
        ui.label(plural(apps, "app")).classes("app-count")

    with ui.card().classes("statement"):
        ui.label("Monthly cost statement").classes("statement-title")

        figure("Hosted alternatives", comparison.avoided_cost)
        bar(
            [
                Segment(
                    price,
                    "seg-hosted",
                    f"{alternative}\n{dollars(price)} / mo",
                    logo=logos.get(alternative, ""),
                )
                for alternative, price in sorted(
                    hosted.items(), key=lambda item: item[1], reverse=True
                )
            ],
            scale,
            ordered=True,
        )

        figure("Self-hosted total", comparison.machine_cost)
        bar(
            [
                Segment(
                    used,
                    "seg-used",
                    f"Applications: {dollars(used)} / mo\nWhat the containers cost to run",
                ),
                Segment(
                    comparison.idle,
                    "seg-idle",
                    f"Idle: {dollars(comparison.idle)} / mo\nCapacity that no container used",
                    text="Idle",
                ),
                Segment(
                    comparison.avoided_cost - comparison.machine_cost,
                    "seg-avoided",
                    f"{dollars(comparison.avoided_cost - comparison.machine_cost)} / mo avoided\nWhat the subscriptions would cost beyond your machine",
                    text=f"{dollars(comparison.avoided_cost - comparison.machine_cost)} / mo avoided",
                ),
            ],
            scale,
        )

    table = (
        ui.table(
            columns=[
                {
                    "name": "app",
                    "label": "Self-hosted app",
                    "field": "app",
                    "align": "left",
                },
                number_column("self_hosted", "Self-hosted cost"),
                {
                    "name": "alternative",
                    "label": "Hosted alternative",
                    "field": "alternative",
                    "align": "left",
                },
                number_column("avoided_cost", "Hosted cost"),
                number_column("difference", "Cost difference"),
            ],
            rows=statement_rows(comparison),
            pagination={"rowsPerPage": 0},
        )
        .classes("w-full")
        .props("hide-bottom")
    )
    table.add_slot("body-cell-app", ROW_WITH_LOGO)
    table.add_slot("body-cell-difference", DIFFERENCE_CELL)

    net = comparison.avoided_cost - comparison.machine_cost
    with ui.row().classes("statement-total w-full justify-between"):
        ui.label("Net per month, against the whole machine").classes("text-sm")
        with ui.row().classes("items-baseline gap-3"):
            ui.label(percent(comparison.roi)).classes(f"text-sm {tone(comparison.roi)}")
            ui.label(money(net)).classes(f"statement-figure {tone(net)}")


@ui.page("/")
async def page_dashboard() -> None:
    config_manager = get_config_manager()
    # the file may have been edited outside of the app since the page was last opened
    _ = config_manager.load()
    layout = create_layout("Dashboard")
    db = get_db()
    config = config_manager.config

    with layout:
        if config is None or not config.stacks:
            no_stacks()
            return

        stack_select = create_stack_select(config)

        @ui.refreshable
        async def result() -> None:
            stack_id = cast(StackId | None, stack_select.value)
            if stack_id is None:
                no_stacks()
                return

            stack = next((x for x in config.stacks if x.id == stack_id), None)
            if stack is None or not offered_sources(stack):
                no_sources()
                return

            costs = await run.io_bound(get_container_cost_rows, db, stack_id)

            if not costs:
                empty_state(
                    "dns",
                    "No Docker data yet",
                    "Sync a docker source on the Integrations page to see what its containers cost and what the subscriptions they replace would.",
                    "Go to Integrations",
                    "/integrations",
                )
                return

            dashboard_view(compare(costs), stack.name)

            for source in offered_sources(stack):
                with ui.card():
                    await application_costs(db, stack_id, source.id)

        stack_select.on_value_change(lambda _: result.refresh())

        await result()
