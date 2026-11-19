from datetime import UTC, datetime
from typing import cast

import pandas as pd

from varne.ui.components.resource_usage import (
    ALL_CONTAINERS,
    SYSTEM,
    UsageName,
    order_metrics,
    parse_usage_names,
    select_series,
)

HOUR = datetime(2026, 11, 19, 10, tzinfo=UTC)


def rows(*items: tuple[str, int]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_time": [HOUR] * len(items),
            "usage_name": [name for name, _ in items],
            "usage": [value for _, value in items],
        }
    )


def test_three_part_names_are_resources():
    assert parse_usage_names(["lab/web/cpu", "lab/system/disk"]) == [
        UsageName("lab", "web", "cpu"),
        UsageName("lab", "system", "disk"),
    ]


def test_other_shapes_are_not_resources():
    assert parse_usage_names(["pageviews", "sessions"]) is None
    assert parse_usage_names(["lab/web/cpu", "pageviews"]) is None
    assert parse_usage_names([]) is None


def test_metrics_come_in_a_fixed_order():
    assert order_metrics(["load", "zzz", "cpu", "disk", "memory"]) == [
        "cpu",
        "memory",
        "disk",
        "load",
        "zzz",
    ]


def test_system_is_the_default_view():
    df = rows(("lab/system/cpu", 5000), ("lab/web/cpu", 100), ("lab/db/cpu", 200))

    selected = select_series(df, "cpu", SYSTEM, several_systems=False)

    assert selected["series"].tolist() == ["lab"]
    assert selected["usage"].tolist() == [50.0]


def test_all_containers_leave_out_the_system_total():
    df = rows(("lab/system/cpu", 5000), ("lab/web/cpu", 100), ("lab/db/cpu", 200))

    selected = select_series(df, "cpu", ALL_CONTAINERS, several_systems=False)

    assert set(cast(list[str], selected["series"].tolist())) == {"db", "web"}


def test_one_container_shows_only_itself():
    df = rows(("lab/web/cpu", 100), ("lab/db/cpu", 200))

    selected = select_series(df, "cpu", "web", several_systems=False)

    assert selected["series"].tolist() == ["web"]
    assert selected["usage"].tolist() == [1.0]


def test_series_carry_the_system_when_there_are_several():
    df = rows(("a/web/memory", 1024**3), ("b/web/memory", 2 * 1024**3))

    selected = select_series(df, "memory", ALL_CONTAINERS, several_systems=True)

    assert selected["series"].tolist() == ["a/web", "b/web"]
    assert selected["usage"].tolist() == [1.0, 2.0]
