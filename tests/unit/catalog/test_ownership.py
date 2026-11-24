from decimal import Decimal

import pytest

from varne.catalog.ownership import duration, ownership, payback
from varne.config import ConfigDocker


def machine(**cost: object) -> ConfigDocker:
    return ConfigDocker.model_validate(
        {
            "id": "lab",
            "name": "Lab",
            "type": "docker",
            "cost": cost,
            "usage": {
                "type": "beszel",
                "url": "http://hub",
                "email": "me@example.com",
                "password": "secret",
            },
        }
    )


OWNED = machine(
    machine_cost=1200,
    amortization_years=6,
    power_draw_watts=40,
    electricity_price_per_kwh="0.2",
)


def test_the_cost_of_owning_is_hardware_and_electricity():
    owned = ownership([OWNED], Decimal("22.5"))

    assert owned is not None
    names = [name for name, _ in owned.lines]
    assert names == ["Hardware amortization", "Electricity"]
    assert sum(cost for _, cost in owned.lines) == pytest.approx(Decimal("22.5"))
    # 1200 over 6 years is $16.67 a month, 40 W at $0.2 is $5.84
    hardware, electricity = (cost for _, cost in owned.lines)
    assert float(hardware) == pytest.approx(16.67, abs=0.1)
    assert float(electricity) == pytest.approx(5.84, abs=0.1)
    assert owned.hardware_price == Decimal(1200)


def test_the_lines_are_scaled_to_what_was_pulled_so_that_they_add_up():
    owned = ownership([OWNED], Decimal(30))

    assert owned is not None
    assert sum(cost for _, cost in owned.lines) == pytest.approx(Decimal(30))


def test_a_machine_that_is_rented_has_a_line_of_its_own_and_no_hardware():
    owned = ownership([machine(hourly_cost="0.05")], Decimal("36.5"))

    assert owned is not None
    assert [name for name, _ in owned.lines] == ["Hosting"]
    assert owned.hardware_price is None
    assert payback(owned, Decimal(100)) is None


def test_one_rented_machine_among_bought_ones_leaves_nothing_to_pay_back():
    owned = ownership([OWNED, machine(hourly_cost="0.05")], Decimal(40))

    assert owned is not None
    assert owned.hardware_price is None
    assert payback(owned, Decimal(100)) is None


def test_two_bought_machines_are_paid_back_together():
    owned = ownership([OWNED, OWNED], Decimal(45))

    assert owned is not None
    assert owned.hardware_price == Decimal(2400)


def test_nothing_is_owned_without_machines():
    assert ownership([], Decimal(10)) is None


def test_the_hardware_pays_back_with_what_is_saved_on_subscriptions():
    owned = ownership([OWNED], Decimal("22.5"))
    assert owned is not None

    result = payback(owned, Decimal("142.5"))

    assert result is not None
    assert result.hardware_price == Decimal(1200)
    # the subscriptions cost 142.5, the machines 22.5: 120 is saved, and 1200 / 120
    assert result.saved_per_month == Decimal(120)
    assert result.months == Decimal(10)


def test_it_never_pays_back_when_the_subscriptions_cost_less_than_the_machines():
    owned = ownership([OWNED], Decimal("22.5"))
    assert owned is not None

    result = payback(owned, Decimal(20))

    assert result is not None
    assert result.saved_per_month < 0
    assert result.months is None


@pytest.mark.parametrize(
    ("months", "words"),
    [
        (Decimal("0.01"), "less than a day"),
        (Decimal("0.1"), "3 days"),
        (Decimal("1"), "1 month"),
        (Decimal("8.4"), "8 months 12 days"),
        (Decimal("12"), "1 year"),
        (Decimal("14.5"), "1 year 2 months 15 days"),
        (Decimal("53.3"), "4 years 5 months 9 days"),
        (Decimal("11.99"), "1 year"),
    ],
)
def test_a_number_of_months_is_said_in_years_months_and_days(
    months: Decimal, words: str
):
    assert duration(months) == words
