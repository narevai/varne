from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

from varne.ui.components.application_costs import cost_per_application
from varne.ui.format import container_label

DAY = datetime(2026, 9, 9, tzinfo=UTC)
SEARX = '{"system": "lab", "image": "searxng/searxng:1"}'
UNKNOWN = '{"system": "lab", "image": "ghcr.io/someone/thing:1"}'


def test_containers_of_one_application_are_added_up():
    df = cost_per_application(
        [
            (
                DAY,
                "photos",
                '{"image": "ghcr.io/immich-app/immich-server:1"}',
                Decimal(2),
            ),
            (
                DAY,
                "ml",
                '{"image": "ghcr.io/immich-app/immich-machine-learning:1"}',
                Decimal(1),
            ),
        ]
    )

    assert df["application"].tolist() == ["Immich"]
    assert df["cost"].tolist() == [3.0]


def test_what_no_container_used_is_a_series_of_its_own():
    df = cost_per_application(
        [(DAY, "Idle", "{}", Decimal(20)), (DAY, "s", SEARX, Decimal(1))]
    )

    costs = dict(
        zip(
            cast(list[str], df["application"].tolist()),
            cast(list[float], df["cost"].tolist()),
            strict=True,
        )
    )
    assert costs == {"Idle": 20.0, "SearXNG": 1.0}


def test_an_application_outside_the_catalog_goes_by_the_name_of_its_image():
    df = cost_per_application(
        [(DAY, "a", UNKNOWN, Decimal(1)), (DAY, "b", UNKNOWN, Decimal(2))]
    )

    assert df["application"].tolist() == ["Thing"]
    assert df["cost"].tolist() == [3.0]


def test_containers_without_an_image_are_grouped_together():
    df = cost_per_application(
        [(DAY, "a", "{}", Decimal(1)), (DAY, "b", "{}", Decimal(2))]
    )

    assert df["application"].tolist() == ["Other"]
    assert df["cost"].tolist() == [3.0]


def test_every_day_is_kept_apart():
    other_day = datetime(2026, 9, 10, tzinfo=UTC)

    df = cost_per_application(
        [(DAY, "s", SEARX, Decimal(1)), (other_day, "s", SEARX, Decimal(2))]
    )

    assert df["cost"].tolist() == [1.0, 2.0]


def test_no_costs_give_an_empty_frame():
    assert cost_per_application([]).empty


def test_only_the_main_container_is_named_in_full_and_the_next_one_cut_short():
    assert container_label(("lab-immich-server-1",)) == "lab-immich-server-1"
    assert (
        container_label(("lab-immich-server-1", "lab-immich-ml-1", "lab-immich-db-1"))
        == "lab-immich-server-1, lab-i…"
    )
