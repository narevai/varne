from decimal import Decimal

from varne.catalog.comparison import AppComparison, Comparison
from varne.catalog.hosted import HOSTED_BY_ID


def comparison(compared: int, not_compared: int) -> Comparison:
    hosted = HOSTED_BY_ID["chatgpt-plus"]
    apps = [
        AppComparison(
            f"compared {i}", None, (f"c{i}",), Decimal(2), hosted, (Decimal(2),)
        )
        for i in range(compared)
    ] + [
        AppComparison(f"other {i}", None, (f"o{i}",), Decimal(1), None, (Decimal(1),))
        for i in range(not_compared)
    ]
    return Comparison(apps, Decimal(100), Decimal(0), Decimal(0), Decimal(730))


def names(compared: int, not_compared: int) -> list[str]:
    # imported here: a page registers itself when its module is loaded
    from varne.ui.pages.dashboard import statement_rows

    return [row["app"] for row in statement_rows(comparison(compared, not_compared))]


def test_compared_fill_the_table_and_a_few_that_are_not_compared_the_rest():
    rows = names(23, 70)

    assert len(rows) == 26
    assert rows[:23] == [f"compared {i}" for i in range(23)]
    assert rows[23:25] == ["other 0", "other 1"]
    assert rows[25] == "68 other apps"


def test_every_compared_app_is_listed_and_those_that_are_not_are_folded():
    rows = names(35, 30)

    assert len(rows) == 36
    assert rows[:35] == [f"compared {i}" for i in range(35)]
    assert rows[35] == "30 other apps"


def test_a_small_table_lists_everything():
    rows = names(5, 10)

    assert len(rows) == 15
    assert not any("other apps" in row for row in rows)
