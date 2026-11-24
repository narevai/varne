"""What owning the machines costs, line by line, and when owning them pays back."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from varne.catalog.comparison import HOURS_PER_MONTH
from varne.config import ConfigDocker
from varne.providers.docker.rates import cost_lines

# The length of a month, for saying how long a number of months is in days.
DAYS_PER_MONTH = Decimal("30.4375")


@dataclass(frozen=True)
class Ownership:
    """The cost of the machines in a month, and what it is made of."""

    # `(name, USD per month)`; together they are the cost of the machines.
    lines: tuple[tuple[str, Decimal], ...]
    total: Decimal
    # What was paid for the hardware. It is not known of machines that are rented by
    # the hour, and then there is nothing that could pay back.
    hardware_price: Decimal | None


@dataclass(frozen=True)
class Payback:
    """When the hardware has paid for itself with the subscriptions it replaces."""

    hardware_price: Decimal
    # What is saved in a month: the subscriptions that are not paid, less what the
    # machines cost, which is the "avoided" of the page.
    saved_per_month: Decimal
    # `None` when nothing is saved, and so it never pays back.
    months: Decimal | None


def ownership(sources: Sequence[ConfigDocker], total: Decimal) -> Ownership | None:
    """The lines of the cost of the machines, in what they sum to.

    The lines come from the configuration and are scaled to `total`, which comes from
    what was pulled, so that the two never show a different sum.
    """
    raw: dict[str, Decimal] = {}
    for source in sources:
        for line in cost_lines(
            source.cost.hourly_cost,
            source.cost.machine_cost,
            source.cost.amortization_years,
            source.cost.power_draw_watts,
            source.cost.electricity_price_per_kwh,
        ):
            raw[line.service_name] = (
                raw.get(line.service_name, Decimal(0))
                + line.cost_per_hour * HOURS_PER_MONTH
            )

    whole = sum(raw.values(), Decimal(0))
    if whole == 0:
        return None

    scale = total / whole
    lines = tuple((name, cost * scale) for name, cost in raw.items())
    prices = [source.cost.machine_cost for source in sources]

    return Ownership(
        lines=lines,
        total=total,
        hardware_price=(
            sum((price for price in prices if price is not None), Decimal(0))
            if all(price is not None for price in prices)
            else None
        ),
    )


def payback(owned: Ownership, avoided_cost: Decimal) -> Payback | None:
    """When the hardware pays back, if there was hardware to pay for."""
    if owned.hardware_price is None:
        return None

    saved = avoided_cost - owned.total
    return Payback(
        hardware_price=owned.hardware_price,
        saved_per_month=saved,
        months=owned.hardware_price / saved if saved > 0 else None,
    )


def duration(months: Decimal) -> str:
    """`8 months 12 days`: a number of months, as years, months and days."""
    whole = int(months)
    days = int((months - whole) * DAYS_PER_MONTH + Decimal("0.5"))
    if days >= 30:
        whole, days = whole + 1, 0
    years, whole = divmod(whole, 12)

    parts = [
        f"{count} {noun}{'' if count == 1 else 's'}"
        for count, noun in ((years, "year"), (whole, "month"), (days, "day"))
        if count
    ]
    return " ".join(parts) or "less than a day"
