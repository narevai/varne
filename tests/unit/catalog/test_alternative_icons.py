from varne.catalog.apps import ALTERNATIVE_ICONS, APPS
from varne.catalog.images import ICON_FILES


def test_a_subscription_logo_is_a_logo_that_ships_with_the_app():
    assert set(ALTERNATIVE_ICONS.values()) <= set(ICON_FILES)


def test_a_subscription_logo_is_for_a_subscription_of_the_catalog():
    assert set(ALTERNATIVE_ICONS) <= {app.alternative for app in APPS}
