from datetime import UTC, datetime, timedelta

import httpx2 as httpx
from tests.unit.providers.test_store import FakeService

from varne.db.types import DatabaseBackend


def ticking_clock():
    ticks = iter(
        datetime(2026, 9, 10, 12, tzinfo=UTC) + timedelta(seconds=i) for i in range(100)
    )
    return lambda: next(ticks)


def response() -> httpx.Response:
    request = httpx.Request("GET", "https://example.com/x")
    return httpx.Response(200, text="{}", request=request)


def test_every_response_of_one_pull_has_the_same_extracted_at(db: DatabaseBackend):
    service = FakeService(db, "stack", "source", now=ticking_clock())

    with service.pull():
        first = service._raw(response())  # pyright: ignore[reportPrivateUsage]
        second = service._raw(response())  # pyright: ignore[reportPrivateUsage]

    assert first.extracted_at == second.extracted_at


def test_each_pull_gets_its_own_extracted_at(db: DatabaseBackend):
    service = FakeService(db, "stack", "source", now=ticking_clock())

    with service.pull():
        first = service._raw(response())  # pyright: ignore[reportPrivateUsage]
    with service.pull():
        second = service._raw(response())  # pyright: ignore[reportPrivateUsage]

    assert second.extracted_at > first.extracted_at


def test_outside_a_pull_the_clock_is_read_every_time(db: DatabaseBackend):
    service = FakeService(db, "stack", "source", now=ticking_clock())

    first = service._raw(response())  # pyright: ignore[reportPrivateUsage]
    second = service._raw(response())  # pyright: ignore[reportPrivateUsage]

    assert second.extracted_at > first.extracted_at


def test_the_pull_ends_even_when_it_fails(db: DatabaseBackend):
    service = FakeService(db, "stack", "source", now=ticking_clock())

    try:
        with service.pull():
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    first = service._raw(response())  # pyright: ignore[reportPrivateUsage]
    second = service._raw(response())  # pyright: ignore[reportPrivateUsage]
    assert second.extracted_at > first.extracted_at


def test_period_covers_today(db: DatabaseBackend):
    service = FakeService(
        db,
        "stack",
        "source",
        lookback_days=3,
        now=lambda: datetime(2026, 9, 10, 15, 30, tzinfo=UTC),
    )

    assert service.period() == (
        datetime(2026, 9, 7, tzinfo=UTC),
        datetime(2026, 9, 11, tzinfo=UTC),
    )
