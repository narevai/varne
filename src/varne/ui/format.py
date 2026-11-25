from decimal import Decimal


def dollars(amount: Decimal | None) -> str:
    if amount is None:
        return "—"

    # a container costs fractions of a cent an hour, cents alone would show $0.00
    if 0 < abs(amount) < Decimal("0.01"):
        return f"${amount:.4f}"

    return f"${amount:,.2f}"


def percent(value: Decimal | None) -> str:
    return "n/a" if value is None else f"{value:+.0%}"


def money(amount: Decimal) -> str:
    """Dollars, with the sign in front of the dollar sign."""
    if amount < 0:
        return f"-{dollars(-amount)}"

    return dollars(amount)


def plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def tone(amount: Decimal | None) -> str:
    if amount is None:
        return ""

    return "text-positive" if amount >= 0 else "text-negative"


SHORT_NAME = 5


def container_label(names: tuple[str, ...]) -> str:
    """The main container in full and the next one cut short; the rest is left out."""
    main, *others = names

    if not others:
        return main

    return f"{main}, {others[0][:SHORT_NAME]}…"
