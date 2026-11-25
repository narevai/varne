from decimal import Decimal
from typing import cast

from nicegui import run, ui
from nicegui.events import GenericEventArguments

from varne.analytics.comparison import get_container_cost_rows
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
from varne.ui.components.amount_line import amount_line
from varne.ui.components.application_costs import application_costs
from varne.ui.components.bar import Segment, bar
from varne.ui.components.empty_state import empty_state, no_sources, no_stacks
from varne.ui.components.stack_select import create_stack_select
from varne.ui.components.statement_table import (
    APPLICATION_CELL,
    DIFFERENCE_CELL,
    HOSTED_CELL,
    number_column,
)
from varne.ui.components.total import total
from varne.ui.format import container_label, dollars, money, plural, tone
from varne.ui.layout import create_layout
from varne.ui.sync import sync_with_notice

# The table lists this many applications, or more when more of them are compared: every
# one that is compared is listed, the ones that are not fill what is left, and the rest
# is folded into one row.
LISTED_ROWS = 25


def statement_rows(
    comparison: Comparison, expanded: bool = False
) -> list[dict[str, str]]:
    compared = [
        app
        for app in comparison.apps
        if app.alternative is not None and app.avoided_cost is not None
    ]
    rest = [app for app in comparison.apps if app not in compared]

    # One subscription stands in for all the applications that share it, and is paid for
    # once: the first of them carries its price, against what all of them cost to run.
    shared_cost: dict[str, Decimal] = {}
    for app in compared:
        if app.hosted is not None:
            shared_cost[app.hosted.id] = (
                shared_cost.get(app.hosted.id, Decimal(0)) + app.self_hosted
            )
    # the application that carries the price of each
    priced: dict[str, str] = {}

    def row(app: AppComparison) -> dict[str, str]:
        assert app.hosted is not None
        payer = priced.setdefault(app.hosted.id, app.app)
        repeated = payer != app.app
        difference = (app.avoided_cost or Decimal(0)) - shared_cost[app.hosted.id]
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
            "avoided_cost": f"Shared with {payer}"
            if repeated
            else dollars(app.avoided_cost),
            "difference": "" if repeated else money(difference),
            "tone": "" if repeated else tone(difference),
        }

    def left_out(
        name: str, symbol: str, cost: Decimal, containers: str, icon: str = ""
    ) -> dict[str, str]:
        return {
            "app": name,
            "icon": icon,
            "symbol": symbol,
            "containers": containers,
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

    # What has nothing to be compared with, one by one: an application of its own, and
    # each container whose image says nothing about what it is.
    singles: list[tuple[Decimal, dict[str, str]]] = []
    for app in rest:
        if app.app == OTHER:
            for name, cost in zip(app.containers, app.container_costs, strict=True):
                singles.append((cost, left_out(name, "apps", cost, "")))
        else:
            icon = f"/ui-assets/icons/{ICON_FILES[app.icon]}" if app.icon else ""
            singles.append(
                (
                    app.self_hosted,
                    left_out(
                        app.app,
                        "apps",
                        app.self_hosted,
                        container_label(app.containers),
                        icon,
                    ),
                )
            )
    singles.sort(key=lambda single: single[0], reverse=True)

    rows = [row(app) for app in compared]
    shown = max(LISTED_ROWS - len(rows), 0)
    rows.extend(single for _, single in singles[:shown])
    hidden = singles[shown:]
    if hidden:
        summary = left_out(
            plural(len(hidden), "other app"),
            "expand_less" if expanded else "expand_more",
            sum((cost for cost, _ in hidden), Decimal(0)),
            "click to hide" if expanded else "click to show",
        )
        # a click on it shows or hides the ones it stands for
        summary["more"] = "yes"
        rows.append(summary)
        if expanded:
            for _, single in hidden:
                # set in a little, under the row that opened them
                single["nested"] = "yes"
                rows.append(single)
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
            amount_line(
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
        lines: list[tuple[str, Decimal]] = (
            list(owned.lines) if owned is not None else []
        )
        total(
            "Total",
            comparison.machine_cost,
            [(LINE_LABELS.get(name, name), cost) for name, cost in lines],
        )

        if owned is not None:
            breakdown(owned, comparison.avoided_cost)

    expanded = False
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
            rows=statement_rows(comparison, expanded),
            pagination={"rowsPerPage": 0},
        )
        .classes("w-full")
        .props("hide-bottom")
    )

    def toggle_hidden(e: GenericEventArguments) -> None:
        nonlocal expanded
        _, row, _ = cast(tuple[object, dict[str, str], object], e.args)
        if row.get("more"):
            expanded = not expanded
            table.rows = statement_rows(comparison, expanded)
            table.update()

    table.on("rowClick", toggle_hidden)
    table.add_slot("body-cell-app", APPLICATION_CELL)
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
                    if await sync_with_notice(stack, offered_sources(stack)):
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
