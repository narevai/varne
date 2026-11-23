from decimal import Decimal
from typing import cast

from nicegui import run, ui

from varne.analytics.comparison import get_container_costs
from varne.catalog.comparison import Comparison, ContainerCost, compare, image_of
from varne.catalog.images import ICON_FILES
from varne.config import StackId
from varne.db.lock import serialized
from varne.db.types import DatabaseBackend
from varne.dependencies import get_config_manager, get_db
from varne.ui.components.container_names import container_label
from varne.ui.components.empty_state import empty_state, no_stacks
from varne.ui.components.stack_select import create_stack_select
from varne.ui.layout import create_layout

ROW_WITH_LOGO = """
<q-td :props="props">
    <div class="row items-center no-wrap" style="gap: 12px">
        <img v-if="props.row.icon" :src="props.row.icon"
             style="width: 28px; height: 28px; flex: none; object-fit: contain" />
        <q-icon v-else name="apps" size="28px" class="opacity-40" />
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
NOTE = "Avoided cost is the price of the most popular plan of the paid counterpart, for one seat, in USD. The machine cost includes idle capacity and applications without a counterpart."


@serialized
def get_container_cost_rows(
    db: DatabaseBackend, stack_id: StackId
) -> list[ContainerCost]:
    df = get_container_costs(db, stack_id).to_pandas()

    return [
        ContainerCost(
            source_id=source_id,
            name=name,
            image=image_of(tags),
            cost=Decimal(str(cost)),
            hours=Decimal(str(hours)),
        )
        for source_id, name, tags, cost, hours in zip(
            cast(list[str], df["source_id"].tolist()),
            cast(list[str], df["service_name"].tolist()),
            cast(list[str], df["tags"].tolist()),
            cast(list[object], df["cost"].tolist()),
            cast(list[object], df["hours"].tolist()),
            strict=True,
        )
    ]


def dollars(amount: Decimal | None) -> str:
    if amount is None:
        return "—"

    # a container costs fractions of a cent an hour, cents alone would show $0.00
    if 0 < abs(amount) < Decimal("0.01"):
        return f"${amount:.4f}"

    return f"${amount:,.2f}"


def percent(value: Decimal | None) -> str:
    return "n/a" if value is None else f"{value:+.0%}"


def stat(label: str, value: str, tone: str = "") -> None:
    with ui.card():
        ui.label(label).classes("text-sm opacity-70")
        ui.label(value).classes(f"text-3xl {tone}")


def tone(amount: Decimal | None) -> str:
    if amount is None:
        return ""

    return "text-positive" if amount >= 0 else "text-negative"


def number_column(name: str, label: str) -> dict[str, str]:
    return {"name": name, "label": label, "field": name, "align": "right"}


def selfhosted_view(comparison: Comparison) -> None:
    with ui.element("div").classes(
        "grid w-full gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-4"
    ):
        stat("Machine cost", dollars(comparison.machine_cost))
        stat("Idle capacity", dollars(comparison.idle))
        stat("Avoided cost", dollars(comparison.avoided_cost))
        stat(
            "Return on investment",
            percent(comparison.roi),
            tone(comparison.roi),
        )

    table = ui.table(
        columns=[
            {"name": "app", "label": "Application", "field": "app", "align": "left"},
            number_column("self_hosted", "Cost of self-hosting"),
            {
                "name": "alternative",
                "label": "Replaces",
                "field": "alternative",
                "align": "left",
            },
            number_column("avoided_cost", "Avoided cost"),
        ],
        rows=[
            {
                "app": app.app,
                "icon": f"/ui-assets/icons/{ICON_FILES[app.icon]}" if app.icon else "",
                "containers": container_label(app.containers),
                "all_containers": "\n".join(app.containers)
                if len(app.containers) > 1
                else "",
                "self_hosted": dollars(app.self_hosted),
                "alternative": app.alternative or "",
                "avoided_cost": dollars(app.avoided_cost),
            }
            for app in comparison.apps
        ],
        pagination={"rowsPerPage": 25},
    ).classes("w-full")
    table.add_slot("body-cell-app", ROW_WITH_LOGO)

    ui.label(NOTE).classes("text-sm opacity-70")


@ui.page("/selfhosted")
async def page_selfhosted() -> None:
    layout = create_layout()
    db = get_db()
    config_manager = get_config_manager()
    config = config_manager.config

    with layout:
        ui.html("<h1>Self-hosted</h1>")

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

            costs = await run.io_bound(get_container_cost_rows, db, stack_id)

            if not costs:
                empty_state(
                    "dns",
                    "No Docker data yet",
                    "Pull a docker source on the Dashboard to see what its containers cost and what the subscriptions they replace would.",
                    "Go to Dashboard",
                    "/",
                )
                return

            selfhosted_view(compare(costs))

        stack_select.on_value_change(lambda _: result.refresh())

        await result()
