from decimal import Decimal
from typing import NamedTuple, cast

from nicegui import run, ui

from varne.catalog.comparison import (
    OTHER,
    AppComparison,
    Comparison,
    compare,
)
from varne.catalog.images import ICON_FILES
from varne.catalog.ownership import Ownership, duration, ownership, payback
from varne.config import ConfigDocker, StackId, offered_sources
from varne.dependencies import get_config_manager, get_db
from varne.ui.components.application_costs import application_costs
from varne.ui.components.container_costs import get_container_cost_rows
from varne.ui.components.container_names import container_label
from varne.ui.components.empty_state import empty_state, no_sources, no_stacks
from varne.ui.components.stack_select import create_stack_select
from varne.ui.components.sync import sync_sources
from varne.ui.components.tip import TIP_ATTRIBUTES, TIP_PROPS, Tip, tip_table
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
                <q-tooltip v-if="props.row.all_containers" class="seg-tip" @tip-attributes>
                    <table class="tip-table">
                        <tr v-for="(name, index) in props.row.all_containers.split('\\n')" :key="name">
                            <td class="key"><div>{{ index === 0 ? 'Containers' : '' }}</div></td>
                            <td class="value"><div>{{ name }}</div></td>
                        </tr>
                    </table>
                </q-tooltip>
            </div>
        </div>
    </div>
</q-td>
""".replace("@tip-attributes", TIP_ATTRIBUTES)
HOSTED_CELL = """
<q-td :props="props">
    <div class="row items-center no-wrap" style="gap: 10px">
        <template v-if="props.row.hosted">
            <img v-if="props.row.hosted_icon" :src="props.row.hosted_icon"
                 :class="props.row.hosted_mono ? 'logo-mono' : ''"
                 style="width: 24px; height: 24px; flex: none; object-fit: contain" />
            <q-icon v-else name="apps" size="24px" class="opacity-40" />
        </template>
        <span>{{ props.value }}</span>
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


def number_column(name: str, label: str, tint: str = "") -> dict[str, str]:
    return {
        "name": name,
        "label": label,
        "field": name,
        "align": "right",
        "classes": tint,
        "headerClasses": tint,
    }


def figure(label: str, value: str, unit: str = "", apart: bool = False) -> None:
    """One line of the profitability: what it is, and what it comes to, on the right.

    A line that is `apart` has a little room above it, to set it off from those before.
    """
    with ui.row().classes(
        "w-full justify-between items-baseline" + (" figure-apart" if apart else "")
    ):
        ui.label(label).classes("text-sm")
        with ui.row().classes("items-baseline gap-1"):
            ui.label(value).classes("statement-figure")
            if unit:
                ui.label(unit).classes("text-sm opacity-60")


def total(label: str, amount: Decimal, rows: list[tuple[str, Decimal]]) -> None:
    """The total of a bar, on a line of its own. Opened, it says what it is made of."""

    def line(name: str, value: Decimal, bold: bool = False) -> None:
        with ui.row().classes("w-full justify-between items-baseline"):
            ui.label(name).classes("text-sm" if not bold else "text-sm font-semibold")
            with ui.row().classes("items-baseline gap-1"):
                ui.label(dollars(value)).classes("statement-figure")
                ui.label("/ mo").classes("text-sm opacity-60")

    if not rows:
        line(label, amount, bold=True)
        return

    with ui.expansion().classes("w-full total-expansion").props("dense") as expansion:
        with expansion.add_slot("header"):
            with ui.row().classes("w-full justify-between items-baseline"):
                ui.label(label).classes("text-sm")
                with ui.row().classes("items-baseline gap-1"):
                    ui.label(dollars(amount)).classes("statement-figure")
                    ui.label("/ mo").classes("text-sm opacity-60")
        with ui.column().classes("total-items w-full gap-1 pb-2"):
            for name, value in rows:
                line(name, value)


class Segment(NamedTuple):
    """One part of a bar: what it is worth, what it says, and what it is."""

    amount: Decimal
    kind: str
    # What is said of it when it is hovered or tapped, as the rows of a table: the name
    # of a field and its value, the way the tooltips of the charts say it.
    tip: Tip
    # Written on it when there is room: the logo, else the text, else the symbol that
    # stands in for a logo.
    text: str = ""
    logo: str = ""
    # A logo drawn in black only, to be shown light on the dark theme.
    mono: bool = False
    placeholder: str = ""


def bar(segments: list[Segment], scale: Decimal, ordered: bool = False) -> None:
    """One bar, on a scale that it shares with the other.

    What is written on a segment is shown where it fits, see theme.py. On an ordered
    bar it stops at the first segment where it does not fit: no segment to its right
    is written on.
    """
    with ui.element("div").classes("bar bar-ordered" if ordered else "bar"):
        for segment in segments:
            if segment.amount <= 0 or scale <= 0:
                continue

            width = f"{float(segment.amount / scale * 100):.2f}%"
            with (
                ui.element("div")
                .classes(f"bar-seg {segment.kind}")
                .style(f"width: {width}")
            ):
                if segment.logo or segment.text or segment.placeholder:
                    with ui.element("div").classes("seg-text"):
                        if segment.logo:
                            ui.element("img").props(f"src={segment.logo}").classes(
                                "seg-logo logo-mono" if segment.mono else "seg-logo"
                            )
                        elif segment.text:
                            ui.label(segment.text)
                        else:
                            ui.icon(segment.placeholder, size="24px").classes(
                                "opacity-40"
                            )
                # a mouse hovers over it, a finger taps it and the tip stays until the next tap
                with ui.tooltip().classes("seg-tip").props(TIP_PROPS):
                    tip_table(segment.tip)
                with (
                    ui.menu()
                    .classes("seg-menu")
                    .props(f"anchor='top middle' self='bottom middle' {TIP_PROPS}")
                ):
                    tip_table(segment.tip)


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
            # the logo of the service, never that of the application
            "hosted": "yes" if app.hosted else "",
            "hosted_icon": (
                f"/ui-assets/icons/{ICON_FILES[app.hosted.icon]}"
                if app.hosted and app.hosted.icon
                else ""
            ),
            "hosted_mono": "yes" if app.hosted and app.hosted.mono else "",
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
            "hosted": "",
            "hosted_icon": "",
            "hosted_mono": "",
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


def app_count(comparison: Comparison) -> int:
    """How many applications run: the containers Varne cannot name count one by one."""
    return sum(
        len(app.containers) if app.app == OTHER else 1 for app in comparison.apps
    )


# What the lines of the cost of a machine are called on the page.
LINE_LABELS = {
    "Hardware amortization": "Cost of hardware",
    "Electricity": "Cost of electricity",
    "Hosting": "Cost of hosting",
}


def breakdown(owned: Ownership, avoided_cost: Decimal) -> None:
    """What the cost of self-hosting is made of, and when the hardware pays back."""
    with ui.column().classes("breakdown"):
        # only hardware that was bought can pay back, not a machine rented by the hour
        result = payback(owned, avoided_cost)
        if result is not None:
            figure(
                "Payback period",
                "never, the subscriptions cost less than the machines"
                if result.months is None
                else duration(result.months),
                apart=True,
            )


def dashboard_view(comparison: Comparison, owned: Ownership | None) -> None:
    # one for each hosted service, however many applications stand in for it
    hosted = {
        app.hosted.id: app.hosted for app in comparison.apps if app.hosted is not None
    }
    scale = max(comparison.avoided_cost, comparison.machine_cost)

    # not in a card: it is what the page is about, and it stands out the more for it
    with ui.column().classes("statement"):
        ui.label("Homelab profitability").classes("statement-title")

        ui.label("Cost of hosted alternatives").classes("statement-section")
        bar(
            [
                Segment(
                    service.usd_per_month,
                    "seg-hosted",
                    (
                        ("Service", service.label),
                        ("Price", f"{dollars(service.usd_per_month)} / mo"),
                    ),
                    # the logo of the service, never that of the application
                    logo=(
                        f"/ui-assets/icons/{ICON_FILES[service.icon]}"
                        if service.icon
                        else ""
                    ),
                    mono=service.mono,
                    placeholder="apps",
                )
                for service in sorted(
                    hosted.values(), key=lambda s: s.usd_per_month, reverse=True
                )
            ],
            scale,
            ordered=True,
        )
        total(
            "Total",
            comparison.avoided_cost,
            [
                (service.label, service.usd_per_month)
                for service in sorted(
                    hosted.values(), key=lambda s: s.usd_per_month, reverse=True
                )
            ],
        )

        ui.label("Cost of self-hosting").classes("statement-section")
        bar(
            [
                # one part for each application, so that it is clear what they are
                *(
                    Segment(
                        app.self_hosted,
                        "seg-used",
                        (
                            ("Application", app.app),
                            ("Cost", f"{dollars(app.self_hosted)} / mo"),
                        ),
                    )
                    for app in sorted(
                        comparison.apps, key=lambda a: a.self_hosted, reverse=True
                    )
                ),
                Segment(
                    comparison.idle,
                    "seg-idle",
                    (("Idle", f"{dollars(comparison.idle)} / mo"),),
                    text="Idle",
                ),
                Segment(
                    comparison.avoided_cost - comparison.machine_cost,
                    "seg-avoided",
                    (
                        (
                            "Avoided",
                            f"{dollars(comparison.avoided_cost - comparison.machine_cost)} / mo",
                        ),
                    ),
                    text=f"{dollars(comparison.avoided_cost - comparison.machine_cost)} / mo avoided",
                ),
            ],
            scale,
        )
        total(
            "Total",
            comparison.machine_cost,
            [
                (LINE_LABELS.get(name, name), cost)
                for name, cost in (owned.lines if owned is not None else [])
            ],
        )

        if owned is not None:
            breakdown(owned, comparison.avoided_cost)

    table = (
        ui.table(
            columns=[
                {
                    "name": "app",
                    "label": "Self-hosted app",
                    "field": "app",
                    "align": "left",
                    "classes": "col-self",
                    "headerClasses": "col-self",
                },
                number_column("self_hosted", "Self-hosted cost", "col-self"),
                {
                    "name": "alternative",
                    "label": "Hosted alternative",
                    "field": "alternative",
                    "align": "left",
                    "classes": "col-hosted",
                    "headerClasses": "col-hosted",
                },
                number_column("avoided_cost", "Hosted cost", "col-hosted"),
                number_column("difference", "Cost difference"),
            ],
            rows=statement_rows(comparison),
            pagination={"rowsPerPage": 0},
        )
        .classes("w-full")
        .props("hide-bottom")
    )
    table.add_slot("body-cell-app", ROW_WITH_LOGO)
    table.add_slot("body-cell-alternative", HOSTED_CELL)
    table.add_slot("body-cell-difference", DIFFERENCE_CELL)


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

        # which stack it is about, and how many applications it has, live in the top bar
        with layout.header_tools:
            apps_badge = ui.label().classes("app-count")
            apps_badge.set_visibility(False)
            stack_select = create_stack_select(config)

        @ui.refreshable
        async def result() -> None:
            apps_badge.set_visibility(False)
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

                async def sync() -> None:
                    ui.notify("Syncing, this can take a moment")
                    if await sync_sources(stack, offered_sources(stack)):
                        await result.refresh()

                empty_state(
                    "dns",
                    "No Docker data yet",
                    "The source is added to this stack but not synced. Sync it to see what its containers cost and what the subscriptions they replace would.",
                    "Sync now",
                    sync,
                )
                return

            comparison = compare(costs)
            apps_badge.set_text(plural(app_count(comparison), "app"))
            apps_badge.set_visibility(True)
            docker = [x for x in offered_sources(stack) if isinstance(x, ConfigDocker)]
            dashboard_view(comparison, ownership(docker, comparison.machine_cost))

            for source in offered_sources(stack):
                with ui.card():
                    await application_costs(db, stack_id, source.id)

        stack_select.on_value_change(lambda _: result.refresh())

        await result()
