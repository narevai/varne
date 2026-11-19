from dataclasses import dataclass
from decimal import Decimal

HOURS_PER_YEAR = Decimal(365 * 24)
WATTS_PER_KILOWATT = Decimal(1000)


@dataclass(frozen=True)
class CostLine:
    service_name: str
    cost_per_hour: Decimal
    quantity_per_hour: Decimal
    unit: str


def hardware_cost_per_hour(
    machine_cost: Decimal, amortization_years: Decimal
) -> Decimal:
    return machine_cost / (amortization_years * HOURS_PER_YEAR)


def electricity_cost_per_hour(
    power_draw_watts: Decimal, price_per_kwh: Decimal
) -> Decimal:
    return power_draw_watts / WATTS_PER_KILOWATT * price_per_kwh


def cost_lines(
    hourly_cost: Decimal | None,
    machine_cost: Decimal | None,
    amortization_years: Decimal,
    power_draw_watts: Decimal | None,
    electricity_price_per_kwh: Decimal | None,
) -> list[CostLine]:
    if hourly_cost is not None:
        return [CostLine("Hosting", hourly_cost, Decimal(1), "hours")]

    assert machine_cost is not None

    lines = [
        CostLine(
            "Hardware amortization",
            hardware_cost_per_hour(machine_cost, amortization_years),
            Decimal(1),
            "hours",
        )
    ]

    if power_draw_watts is not None and electricity_price_per_kwh is not None:
        lines.append(
            CostLine(
                "Electricity",
                electricity_cost_per_hour(power_draw_watts, electricity_price_per_kwh),
                power_draw_watts / WATTS_PER_KILOWATT,
                "kWh",
            )
        )

    return lines
