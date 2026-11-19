from decimal import Decimal

from varne.providers.selfhosted.rates import (
    cost_lines,
    electricity_cost_per_hour,
    hardware_cost_per_hour,
)


def test_machine_cost_is_split_over_years_days_and_hours():
    # 6 years * 365 days * 24 hours = 52 560 hours
    assert hardware_cost_per_hour(Decimal(52560), Decimal(6)) == Decimal(1)
    total = hardware_cost_per_hour(Decimal(6000), Decimal(6)) * 52560
    assert total.quantize(Decimal("0.000001")) == Decimal(6000)


def test_electricity_is_kilowatts_times_the_price():
    assert electricity_cost_per_hour(Decimal(100), Decimal("0.30")) == Decimal("0.03")


def test_hardware_mode_has_amortization_and_electricity_lines():
    lines = cost_lines(
        hourly_cost=None,
        machine_cost=Decimal(52560),
        amortization_years=Decimal(6),
        power_draw_watts=Decimal(200),
        electricity_price_per_kwh=Decimal("0.5"),
    )

    assert [
        (line.service_name, line.cost_per_hour, line.quantity_per_hour, line.unit)
        for line in lines
    ] == [
        ("Hardware amortization", Decimal(1), Decimal(1), "hours"),
        ("Electricity", Decimal("0.1"), Decimal("0.2"), "kWh"),
    ]


def test_hardware_mode_without_power_has_no_electricity_line():
    lines = cost_lines(None, Decimal(52560), Decimal(6), None, None)

    assert [line.service_name for line in lines] == ["Hardware amortization"]


def test_hourly_mode_is_a_single_line():
    lines = cost_lines(Decimal("0.35"), None, Decimal(6), None, None)

    assert [(line.service_name, line.cost_per_hour, line.unit) for line in lines] == [
        ("Hosting", Decimal("0.35"), "hours")
    ]
