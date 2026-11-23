from decimal import Decimal

from varne.catalog.comparison import ContainerCost, compare, image_of


def cost(
    name: str,
    image: str | None,
    amount: str,
    hours: str = "730",
    source: str = "lab",
) -> ContainerCost:
    return ContainerCost(source, name, image, Decimal(amount), Decimal(hours))


def test_a_recognised_application_is_compared_with_its_subscription():
    comparison = compare(
        [
            cost("photos", "ghcr.io/immich-app/immich-server:release", "4", "300"),
            cost(
                "photos-ml", "ghcr.io/immich-app/immich-machine-learning:x", "2", "200"
            ),
            cost("Idle", None, "14", "230"),
        ]
    )

    (app,) = comparison.apps
    assert app.app == "Immich"
    assert app.alternative == "iCloud+ 2 TB"
    assert app.self_hosted == Decimal(6)
    # the machine ran for 730 hours: one month of the subscription
    assert app.avoided_cost == Decimal("9.99")


def test_the_investment_is_the_whole_machine_idle_and_unknown_included():
    comparison = compare(
        [
            cost("search", "searxng/searxng:1", "3", "300"),
            cost("mystery", "ghcr.io/someone/thing:1", "5", "300"),
            cost("Idle", None, "12", "130"),
        ]
    )

    assert comparison.machine_cost == Decimal(20)
    assert comparison.avoided_cost == Decimal(10)
    assert comparison.roi == Decimal("-0.5")


def test_machines_running_side_by_side_do_not_double_the_subscription():
    comparison = compare(
        [
            cost("search", "searxng/searxng:1", "3", "730", source="a"),
            cost("search", "searxng/searxng:1", "3", "730", source="b"),
        ]
    )

    assert comparison.avoided_cost == Decimal(10)
    assert comparison.apps[0].self_hosted == Decimal(6)


def test_apps_are_listed_by_what_they_cost_to_run():
    comparison = compare(
        [
            cost("search", "searxng/searxng:1", "1"),
            cost("chat", "ghcr.io/open-webui/open-webui:1", "9"),
        ]
    )

    assert [app.app for app in comparison.apps] == ["Open WebUI", "SearXNG"]


def test_an_application_without_a_counterpart_is_listed_with_its_cost():
    comparison = compare(
        [
            cost("tv", "lscr.io/linuxserver/sonarr:latest", "6", "100"),
            cost("Idle", None, "94", "630"),
        ]
    )

    (app,) = comparison.apps
    assert app.app == "Sonarr"
    assert app.self_hosted == Decimal(6)
    assert app.alternative is None
    assert app.avoided_cost is None
    assert comparison.avoided_cost == Decimal(0)
    assert comparison.idle == Decimal(94)
    assert comparison.machine_cost == Decimal(100)


def test_an_application_lists_the_containers_it_runs_in():
    comparison = compare(
        [
            cost(
                "lab-immich-ml-1", "ghcr.io/immich-app/immich-machine-learning:1", "1"
            ),
            cost("lab-immich-server-1", "ghcr.io/immich-app/immich-server:1", "2"),
        ]
    )

    (app,) = comparison.apps
    # the one that costs most comes first
    assert app.containers == ("lab-immich-server-1", "lab-immich-ml-1")


def test_a_container_without_an_image_is_listed_as_other():
    comparison = compare([cost("mystery", None, "3")])

    (app,) = comparison.apps
    assert app.app == "Other"
    assert app.icon is None


def test_costs_are_scaled_to_a_month_and_subscriptions_are_not():
    # 365 hours is half a month: everything that cost is twice that in a month
    comparison = compare(
        [
            cost("search", "searxng/searxng:1", "3", "100"),
            cost("Idle", None, "7", "265"),
        ]
    )

    (app,) = comparison.apps
    assert app.self_hosted == Decimal(6)
    assert app.avoided_cost == Decimal(10)
    assert comparison.machine_cost == Decimal(20)
    assert comparison.avoided_cost == Decimal(10)
    assert comparison.roi == Decimal("-0.5")


def test_one_subscription_replacing_several_applications_counts_once():
    comparison = compare(
        [
            cost("chat", "ghcr.io/open-webui/open-webui:1", "1"),
            cost("llm", "mintplexlabs/anything-llm:1", "1"),
        ]
    )

    assert [app.avoided_cost for app in comparison.apps] == [Decimal(20), Decimal(20)]
    assert comparison.avoided_cost == Decimal(20)


def test_the_period_is_how_long_the_machine_ran():
    comparison = compare([cost("Idle", None, "5", "48")])

    assert comparison.hours == Decimal(48)
    assert comparison.days == Decimal(2)


def test_without_cost_there_is_no_return():
    comparison = compare([])

    assert comparison.apps == []
    assert comparison.roi is None


def test_the_image_comes_from_the_tags_of_a_row():
    assert image_of('{"system": "lab", "image": "nginx:1"}') == "nginx:1"
    assert image_of('{"system": "lab"}') is None
    assert image_of("{}") is None
