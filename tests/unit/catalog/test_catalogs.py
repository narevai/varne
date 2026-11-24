"""The three catalogs: self-hosted applications, hosted ones, and which stands in for which."""

from decimal import Decimal

from varne.catalog.equivalents import EQUIVALENTS, equivalent_of
from varne.catalog.hosted import HOSTED, HOSTED_BY_ID
from varne.catalog.images import ICON_FILES
from varne.catalog.selfhosted import SELF_HOSTED


def test_a_self_hosted_application_is_known_by_its_images():
    slugs = [slug for app in SELF_HOSTED for slug in app.slugs]

    assert all(app.slugs for app in SELF_HOSTED)
    assert len(slugs) == len(set(slugs))
    assert len({app.name for app in SELF_HOSTED}) == len(SELF_HOSTED)


def test_a_hosted_application_has_a_price_a_source_and_a_name():
    assert len({app.id for app in HOSTED}) == len(HOSTED)
    assert all(app.usd_per_month > Decimal(0) for app in HOSTED)
    assert all(app.source.startswith("https://") for app in HOSTED)
    assert all(app.name and app.label for app in HOSTED)


def test_the_logos_are_logos_that_ship_with_the_app():
    missing = [
        app.name
        for app in (*SELF_HOSTED, *HOSTED)
        if app.icon is not None and app.icon not in ICON_FILES
    ]

    assert missing == []


def test_what_stands_in_for_what_is_in_the_catalogs():
    names = {app.name for app in SELF_HOSTED}

    assert set(EQUIVALENTS) <= names
    assert set(EQUIVALENTS.values()) <= set(HOSTED_BY_ID)


def test_every_hosted_application_is_stood_in_for_by_something():
    assert set(EQUIVALENTS.values()) == set(HOSTED_BY_ID)


def test_the_logo_of_a_hosted_application_is_that_of_the_service():
    chatgpt = HOSTED_BY_ID["chatgpt-plus"]

    assert (chatgpt.label, chatgpt.icon, chatgpt.usd_per_month) == (
        "ChatGPT Plus",
        "chatgpt",
        Decimal(20),
    )
    # the applications that replace it keep their own logos
    stand_in = [app for app in SELF_HOSTED if equivalent_of(app) == chatgpt]
    assert {app.name for app in stand_in} >= {"Open WebUI"}
    assert all(app.icon != chatgpt.icon for app in stand_in)


def test_a_black_logo_is_a_logo_of_a_hosted_application():
    assert {app.icon for app in HOSTED if app.mono} == {"tailscale", "vercel"}
